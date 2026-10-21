import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["NOTIFY_MODE"] = "log"
from app import create_app  # noqa: E402
import security  # noqa: E402

USER = dict(nome="Maria da Silva", cpf="529.982.247-25", nascimento="10 / 05 / 1990",
            celular="(44) 99999-0000", email="maria@example.com",
            endereco="Rua A, 10, Centro, Maringá/PR", senha="senhaSegura1")


class ApiTest(unittest.TestCase):
    def setUp(self):
        security._FAILS.clear()
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self.tmp.name
        self.app = create_app({"TESTING": True})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def auth(self):
        r = self.c.post("/api/auth/register", json=USER)
        self.assertEqual(r.status_code, 201, r.json)
        return {"Authorization": "Bearer " + r.json["token"]}

    def test_frontend_served(self):
        self.assertIn(b"Restaurante Sabor Caseiro", self.c.get("/").data)
        self.assertEqual(self.c.get("/style.css").status_code, 200)
        self.assertEqual(self.c.get("/app.js").status_code, 200)

    def test_menu_and_order_uses_server_prices(self):
        menu = self.c.get("/api/menu").json
        self.assertEqual(len(menu), 8)
        r = self.c.post("/api/orders", json={"mesa": "Mesa 02", "itens": [{"id": menu[0]["id"], "qtd": 2}], "total": 1})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["total_centavos"], 2 * menu[0]["preco_centavos"])
        self.assertEqual(self.c.post("/api/orders", json={"mesa": "", "itens": []}).status_code, 400)
        self.assertEqual(self.c.post("/api/orders", json={"mesa": "1", "itens": [{"id": 999, "qtd": 1}]}).status_code, 400)
        self.assertEqual(self.c.post("/api/orders", json={"mesa": "1", "itens": [{"id": 1, "qtd": -3}]}).status_code, 400)

    def test_register_login_validation(self):
        self.auth()
        self.assertEqual(self.c.post("/api/auth/register", json=USER).status_code, 409)
        bad = dict(USER, cpf="111.111.111-11", email="x@y.com")
        self.assertEqual(self.c.post("/api/auth/register", json=bad).status_code, 400)
        self.assertEqual(self.c.post("/api/auth/register", json=dict(USER, senha="123", email="o@o.com", cpf="52998224725")).status_code, 400)
        ok = self.c.post("/api/auth/login", json={"identificador": "529.982.247-25", "senha": USER["senha"]})
        self.assertEqual(ok.status_code, 200)
        ok2 = self.c.post("/api/auth/login", json={"identificador": "MARIA@example.com", "senha": USER["senha"]})
        self.assertEqual(ok2.status_code, 200)
        self.assertEqual(self.c.post("/api/auth/login", json={"identificador": "maria@example.com", "senha": "errada"}).status_code, 401)

    def test_login_rate_limit(self):
        self.auth()
        for _ in range(5):
            self.c.post("/api/auth/login", json={"identificador": "maria@example.com", "senha": "x"})
        r = self.c.post("/api/auth/login", json={"identificador": "maria@example.com", "senha": USER["senha"]})
        self.assertEqual(r.status_code, 429)

    def test_protected_routes(self):
        for path in ("/api/me", "/api/contacts", "/api/evidences", "/api/alerts"):
            self.assertEqual(self.c.get(path).status_code, 401)
        self.assertEqual(self.c.get("/api/me", headers={"Authorization": "Bearer lixo"}).status_code, 401)

    def test_contacts_and_alert(self):
        h = self.auth()
        self.assertEqual(self.c.post("/api/contacts", json={"nome": "Ana", "telefone": "123"}, headers=h).status_code, 400)
        r = self.c.post("/api/contacts", json={"nome": "Ana Souza", "vinculo": "Amiga", "telefone": "(44) 98888-2222"}, headers=h)
        self.assertEqual(r.status_code, 201)
        a = self.c.post("/api/alerts", json={"lat": -23.4209, "lng": -51.9330}, headers=h)
        self.assertEqual(a.status_code, 201)
        self.assertEqual(a.json["contatos"], 1)
        self.assertIn("wa.me/5544988882222", a.json["links"][0]["url"])
        self.assertEqual(self.c.post("/api/alerts", json={"lat": 999, "lng": 0}, headers=h).status_code, 400)
        self.assertEqual(len(self.c.get("/api/alerts", headers=h).json), 1)

    def test_vault_encrypt_download_isolation(self):
        h = self.auth()
        data = b"conteudo-secreto-do-audio"
        r = self.c.post("/api/evidences", headers=h, content_type="multipart/form-data",
                        data={"titulo": "Áudio", "nota": "ameaça", "arquivo": (io.BytesIO(data), "a.mp3", "audio/mpeg")})
        self.assertEqual(r.status_code, 201, r.json)
        eid = r.json["id"]
        on_disk = b"".join(p.read_bytes() for p in (self.app.config["VAULT_DIR"]).iterdir())
        self.assertNotIn(data, on_disk)  # criptografado em repouso
        self.assertEqual(self.c.get(f"/api/evidences/{eid}/download", headers=h).data, data)
        bad = self.c.post("/api/evidences", headers=h, content_type="multipart/form-data",
                          data={"titulo": "x", "arquivo": (io.BytesIO(b"MZ"), "v.exe", "application/x-msdownload")})
        self.assertEqual(bad.status_code, 400)
        # outra usuária não acessa
        other = self.c.post("/api/auth/register", json=dict(USER, cpf="111.444.777-35", email="b@b.com")).json["token"]
        h2 = {"Authorization": "Bearer " + other}
        self.assertEqual(self.c.get(f"/api/evidences/{eid}/download", headers=h2).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/evidences/{eid}", headers=h2).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/evidences/{eid}", headers=h).status_code, 200)

    def test_rag(self):
        h = self.auth()
        r = self.c.post("/api/rag", json={"pergunta": "Como pedir medida protetiva?"}, headers=h).json
        self.assertIn("medida protetiva", r["resposta"].lower())
        r = self.c.post("/api/rag", json={"pergunta": "onde fica a DEAM em Maringá?"}, headers=h).json
        self.assertIn("DEAM", r["resposta"])
        r = self.c.post("/api/rag", json={"pergunta": "receita de bolo de cenoura"}, headers=h).json
        self.assertIn("190", r["resposta"])

    def test_password_change_and_delete_account(self):
        h = self.auth()
        self.assertEqual(self.c.post("/api/me/password", json={"senha_atual": "errada", "nova_senha": "novaSenha123"}, headers=h).status_code, 403)
        self.assertEqual(self.c.post("/api/me/password", json={"senha_atual": USER["senha"], "nova_senha": "novaSenha123"}, headers=h).status_code, 200)
        self.assertEqual(self.c.post("/api/auth/login", json={"identificador": "maria@example.com", "senha": "novaSenha123"}).status_code, 200)
        self.assertEqual(self.c.delete("/api/me", headers=h).status_code, 200)
        self.assertEqual(self.c.get("/api/me", headers=h).status_code, 401)


if __name__ == "__main__":
    unittest.main()
