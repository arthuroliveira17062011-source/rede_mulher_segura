import io
import os
import secrets
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, g, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

import db as dbm
import notifier
import security as sec
from rag import LocalRAG

BASE = Path(__file__).parent
MAX_UPLOAD = 25 * 1024 * 1024
ALLOWED_MIME_PREFIX = ("image/", "audio/", "video/")
ALLOWED_MIME_EXACT = {"application/pdf", "text/plain"}


def _load_env_file():
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _persistent_secret(path: Path, factory):
    if not path.exists():
        path.write_text(factory())
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return path.read_text().strip()


def create_app(test_config=None):
    _load_env_file()
    app = Flask(__name__, static_folder=str(BASE / "public"), static_url_path="")
    data_dir = Path(os.environ.get("DATA_DIR", BASE / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "vault").mkdir(exist_ok=True)

    app.config.update(
        DATABASE=str(data_dir / "app.db"),
        VAULT_DIR=data_dir / "vault",
        MAX_CONTENT_LENGTH=MAX_UPLOAD + 1024 * 1024,
        SECRET_KEY=os.environ.get("SECRET_KEY")
        or _persistent_secret(data_dir / ".secret_key", lambda: secrets.token_hex(32)),
    )
    ev_key = os.environ.get("EVIDENCE_KEY") or _persistent_secret(
        data_dir / ".evidence.key", lambda: Fernet.generate_key().decode()
    )
    app.config["FERNET"] = Fernet(ev_key.encode())
    if test_config:
        app.config.update(test_config)

    dbm.init_db(app)
    app.teardown_appcontext(dbm.close_db)
    rag = LocalRAG(str(BASE / "data" / "knowledge.json"))

    # ---------------- cabeçalhos de segurança ----------------
    @app.after_request
    def headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if os.environ.get("SECURE_HEADERS_HSTS") == "1":
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(413)
    def too_big(_e):
        return jsonify(erro="Arquivo muito grande (máx. 25 MB)."), 413

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return jsonify(erro="Não encontrado."), 404
        return send_from_directory(app.static_folder, "index.html")

    def body():
        return request.get_json(silent=True) or {}

    def s(v, n=200):
        return (v or "").strip()[:n] if isinstance(v, str) else ""

    # ---------------- frontend ----------------
    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    # ================= RESTAURANTE (público) =================
    @app.get("/api/menu")
    def menu():
        rows = dbm.get_db().execute(
            "SELECT id, categoria, nome, descricao, preco_centavos FROM menu_items WHERE ativo=1 ORDER BY id"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/orders")
    def create_order():
        d = body()
        mesa = s(d.get("mesa"), 40)
        itens = d.get("itens")
        if not mesa:
            return jsonify(erro="Informe o número da mesa."), 400
        if not isinstance(itens, list) or not itens or len(itens) > 50:
            return jsonify(erro="Pedido vazio."), 400
        conn = dbm.get_db()
        lines, total = [], 0
        for it in itens:
            try:
                mid, qtd = int(it.get("id")), int(it.get("qtd"))
            except (TypeError, ValueError, AttributeError):
                return jsonify(erro="Item inválido."), 400
            if not 1 <= qtd <= 50:
                return jsonify(erro="Quantidade inválida."), 400
            row = conn.execute(
                "SELECT id, nome, preco_centavos FROM menu_items WHERE id=? AND ativo=1", (mid,)
            ).fetchone()
            if not row:
                return jsonify(erro="Item inexistente."), 400
            lines.append((row["id"], row["nome"], qtd, row["preco_centavos"]))
            total += qtd * row["preco_centavos"]  # preço SEMPRE vem do servidor
        cur = conn.execute("INSERT INTO orders (mesa, total_centavos) VALUES (?,?)", (mesa, total))
        conn.executemany(
            "INSERT INTO order_items (order_id, menu_item_id, nome, qtd, preco_centavos) VALUES (?,?,?,?,?)",
            [(cur.lastrowid, *ln) for ln in lines],
        )
        conn.commit()
        return jsonify(id=cur.lastrowid, mesa=mesa, total_centavos=total, status="recebido"), 201

    # ================= AUTENTICAÇÃO =================
    def user_json(u):
        return {"id": u["id"], "nome": u["nome"], "email": u["email"]}

    @app.post("/api/auth/register")
    def register():
        d = body()
        nome, email = s(d.get("nome"), 120), s(d.get("email"), 254).lower()
        endereco, senha = s(d.get("endereco"), 250), d.get("senha")
        cpf = sec.only_digits(d.get("cpf"))
        nasc = sec.parse_birth(d.get("nascimento"))
        cel = sec.normalize_phone(d.get("celular"))
        if len(nome) < 3:
            return jsonify(erro="Informe o nome completo."), 400
        if not sec.valid_cpf(cpf):
            return jsonify(erro="CPF inválido."), 400
        if not nasc:
            return jsonify(erro="Data de nascimento inválida (use dd/mm/aaaa)."), 400
        if not cel:
            return jsonify(erro="Celular inválido (use DDD + número)."), 400
        if not sec.valid_email(email):
            return jsonify(erro="E-mail inválido."), 400
        if len(endereco) < 5:
            return jsonify(erro="Informe o endereço."), 400
        if (p := sec.password_problem(senha)):
            return jsonify(erro=p), 400
        conn = dbm.get_db()
        if conn.execute("SELECT 1 FROM users WHERE cpf=? OR email=?", (cpf, email)).fetchone():
            return jsonify(erro="Já existe cadastro com este CPF ou e-mail."), 409
        cur = conn.execute(
            "INSERT INTO users (nome,cpf,email,nascimento,celular,endereco,senha_hash) VALUES (?,?,?,?,?,?,?)",
            (nome, cpf, email, nasc, cel, endereco, sec.hash_password(senha)),
        )
        conn.commit()
        u = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(token=sec.make_token(u["id"]), usuario=user_json(u)), 201

    @app.post("/api/auth/login")
    def login():
        d = body()
        ident = s(d.get("identificador"), 254).lower()
        senha = d.get("senha") if isinstance(d.get("senha"), str) else ""
        key = sec.rate_key(ident)
        if sec.is_locked(key):
            return jsonify(erro="Muitas tentativas. Aguarde alguns minutos."), 429
        digits = sec.only_digits(ident)
        conn = dbm.get_db()
        u = conn.execute(
            "SELECT * FROM users WHERE email=? OR cpf=?", (ident, digits if len(digits) == 11 else "-")
        ).fetchone()
        if not sec.verify_password(senha, u["senha_hash"] if u else None):
            sec.register_fail(key)
            return jsonify(erro="Credenciais inválidas."), 401
        sec.clear_fails(key)
        return jsonify(token=sec.make_token(u["id"]), usuario=user_json(u))

    @app.get("/api/me")
    @sec.login_required
    def me():
        u = dbm.get_db().execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
        if not u:
            return jsonify(erro="Sessão inválida."), 401
        return jsonify(user_json(u))

    @app.post("/api/me/password")
    @sec.login_required
    def change_password():
        d = body()
        conn = dbm.get_db()
        u = conn.execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
        if not u or not sec.verify_password(d.get("senha_atual") or "", u["senha_hash"]):
            return jsonify(erro="Senha atual incorreta."), 403
        if (p := sec.password_problem(d.get("nova_senha"))):
            return jsonify(erro=p), 400
        conn.execute("UPDATE users SET senha_hash=? WHERE id=?", (sec.hash_password(d["nova_senha"]), g.user_id))
        conn.commit()
        return jsonify(ok=True)

    # ================= CONTATOS DE CONFIANÇA =================
    @app.get("/api/contacts")
    @sec.login_required
    def list_contacts():
        rows = dbm.get_db().execute(
            "SELECT id, nome, vinculo, telefone FROM contacts WHERE user_id=? ORDER BY id", (g.user_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/contacts")
    @sec.login_required
    def add_contact():
        d = body()
        nome, vinculo = s(d.get("nome"), 100), s(d.get("vinculo"), 60)
        tel = sec.normalize_phone(d.get("telefone"))
        if len(nome) < 2:
            return jsonify(erro="Informe o nome."), 400
        if not tel:
            return jsonify(erro="Telefone inválido (use DDD + número)."), 400
        conn = dbm.get_db()
        if conn.execute("SELECT COUNT(*) FROM contacts WHERE user_id=?", (g.user_id,)).fetchone()[0] >= 10:
            return jsonify(erro="Limite de 10 contatos."), 400
        cur = conn.execute(
            "INSERT INTO contacts (user_id,nome,vinculo,telefone) VALUES (?,?,?,?)", (g.user_id, nome, vinculo, tel)
        )
        conn.commit()
        return jsonify(id=cur.lastrowid, nome=nome, vinculo=vinculo, telefone=tel), 201

    @app.delete("/api/contacts/<int:cid>")
    @sec.login_required
    def del_contact(cid):
        conn = dbm.get_db()
        cur = conn.execute("DELETE FROM contacts WHERE id=? AND user_id=?", (cid, g.user_id))
        conn.commit()
        return (jsonify(ok=True), 200) if cur.rowcount else (jsonify(erro="Não encontrado."), 404)

    # ================= ALERTA DE EMERGÊNCIA =================
    @app.post("/api/alerts")
    @sec.login_required
    def trigger_alert():
        d = body()
        lat, lng = d.get("lat"), d.get("lng")
        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
        except (TypeError, ValueError):
            return jsonify(erro="Coordenadas inválidas."), 400
        if (lat is None) != (lng is None) or (lat is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180)):
            return jsonify(erro="Coordenadas inválidas."), 400
        conn = dbm.get_db()
        u = conn.execute("SELECT nome FROM users WHERE id=?", (g.user_id,)).fetchone()
        contacts = [dict(r) for r in conn.execute(
            "SELECT nome, telefone FROM contacts WHERE user_id=?", (g.user_id,)).fetchall()]
        result = notifier.notify_contacts(u["nome"], contacts, lat, lng)
        cur = conn.execute(
            "INSERT INTO alerts (user_id,lat,lng,contatos_notificados) VALUES (?,?,?,?)",
            (g.user_id, lat, lng, len(contacts)),
        )
        conn.commit()
        return jsonify(
            id=cur.lastrowid, lat=lat, lng=lng, contatos=len(contacts),
            entregues=result["entregues"], links=result["links"],
        ), 201

    @app.get("/api/alerts")
    @sec.login_required
    def list_alerts():
        rows = dbm.get_db().execute(
            "SELECT id, lat, lng, contatos_notificados, created_at FROM alerts WHERE user_id=? ORDER BY id DESC LIMIT 50",
            (g.user_id,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    # ================= COFRE DE EVIDÊNCIAS =================
    def ev_json(r):
        return {k: r[k] for k in ("id", "titulo", "nota", "arquivo_nome", "arquivo_mime", "arquivo_tamanho", "created_at")}

    @app.get("/api/evidences")
    @sec.login_required
    def list_ev():
        rows = dbm.get_db().execute("SELECT * FROM evidences WHERE user_id=? ORDER BY id DESC", (g.user_id,)).fetchall()
        return jsonify([ev_json(r) for r in rows])

    @app.post("/api/evidences")
    @sec.login_required
    def add_ev():
        titulo, nota = s(request.form.get("titulo"), 120), s(request.form.get("nota"), 5000)
        f = request.files.get("arquivo")
        if not titulo:
            return jsonify(erro="Informe um título."), 400
        if not f and not nota:
            return jsonify(erro="Envie um arquivo ou escreva um relato."), 400
        nome = mime = blob = None
        size = None
        if f and f.filename:
            mime = (f.mimetype or "").lower()
            if not (mime.startswith(ALLOWED_MIME_PREFIX) or mime in ALLOWED_MIME_EXACT):
                return jsonify(erro="Tipo de arquivo não permitido (use foto, áudio, vídeo, PDF ou texto)."), 400
            raw = f.read()
            if len(raw) > MAX_UPLOAD:
                return jsonify(erro="Arquivo muito grande (máx. 25 MB)."), 413
            blob = uuid.uuid4().hex + ".enc"
            (app.config["VAULT_DIR"] / blob).write_bytes(app.config["FERNET"].encrypt(raw))
            nome, size = secure_filename(f.filename) or "arquivo", len(raw)
        conn = dbm.get_db()
        cur = conn.execute(
            "INSERT INTO evidences (user_id,titulo,nota,arquivo_nome,arquivo_mime,arquivo_tamanho,arquivo_blob) VALUES (?,?,?,?,?,?,?)",
            (g.user_id, titulo, nota, nome, mime, size, blob),
        )
        conn.commit()
        r = conn.execute("SELECT * FROM evidences WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(ev_json(r)), 201

    def _own_ev(eid):
        return dbm.get_db().execute("SELECT * FROM evidences WHERE id=? AND user_id=?", (eid, g.user_id)).fetchone()

    @app.get("/api/evidences/<int:eid>/download")
    @sec.login_required
    def dl_ev(eid):
        r = _own_ev(eid)
        if not r or not r["arquivo_blob"]:
            return jsonify(erro="Não encontrado."), 404
        try:
            raw = app.config["FERNET"].decrypt((app.config["VAULT_DIR"] / r["arquivo_blob"]).read_bytes())
        except (InvalidToken, FileNotFoundError):
            return jsonify(erro="Arquivo indisponível."), 410
        return send_file(io.BytesIO(raw), mimetype=r["arquivo_mime"], as_attachment=True, download_name=r["arquivo_nome"])

    @app.delete("/api/evidences/<int:eid>")
    @sec.login_required
    def del_ev(eid):
        r = _own_ev(eid)
        if not r:
            return jsonify(erro="Não encontrado."), 404
        if r["arquivo_blob"]:
            (app.config["VAULT_DIR"] / r["arquivo_blob"]).unlink(missing_ok=True)
        conn = dbm.get_db()
        conn.execute("DELETE FROM evidences WHERE id=?", (eid,))
        conn.commit()
        return jsonify(ok=True)

    # ================= ASSISTENTE RAG LOCAL =================
    @app.post("/api/rag")
    @sec.login_required
    def rag_ask():
        q = s(body().get("pergunta"), 500)
        if len(q) < 3:
            return jsonify(erro="Digite sua pergunta."), 400
        return jsonify(rag.answer(q))  # nada é armazenado nem enviado a terceiros

    # ================= LGPD: excluir conta e dados =================
    @app.delete("/api/me")
    @sec.login_required
    def delete_me():
        conn = dbm.get_db()
        for r in conn.execute("SELECT arquivo_blob FROM evidences WHERE user_id=? AND arquivo_blob IS NOT NULL", (g.user_id,)):
            (app.config["VAULT_DIR"] / r["arquivo_blob"]).unlink(missing_ok=True)
        conn.execute("DELETE FROM users WHERE id=?", (g.user_id,))
        conn.commit()
        return jsonify(ok=True)

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    create_app().run(host="127.0.0.1", port=port, debug=False)
