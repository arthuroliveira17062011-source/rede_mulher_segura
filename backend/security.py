import re
import time
import datetime as dt
from functools import wraps

import jwt
from flask import request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

JWT_HOURS = 8
_DUMMY_HASH = generate_password_hash("dummy-password-for-timing")


def hash_password(pw: str) -> str:
    return generate_password_hash(pw)


def verify_password(pw: str, pw_hash) -> bool:
    # Roda sempre um hash para não revelar (por tempo) se a conta existe.
    return check_password_hash(pw_hash or _DUMMY_HASH, pw) and bool(pw_hash)


def make_token(user_id: int) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + dt.timedelta(hours=JWT_HOURS)}
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify(erro="Não autenticado."), 401
        try:
            data = jwt.decode(auth[7:], current_app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user_id = int(data["sub"])
        except (jwt.PyJWTError, ValueError, KeyError):
            return jsonify(erro="Sessão inválida ou expirada."), 401
        return fn(*a, **kw)
    return wrapper


# ---------- validações ----------
def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def valid_cpf(cpf: str) -> bool:
    d = only_digits(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        s = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (s * 10 % 11) % 10 != int(d[n]):
            return False
    return True


def valid_email(e: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e or "")) and len(e) <= 254


def parse_birth(s: str):
    """Aceita dd/mm/aaaa (com ou sem espaços) ou aaaa-mm-dd. Retorna ISO ou None."""
    s = (s or "").replace(" ", "")
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(s, fmt).date()
            age = (dt.date.today() - d).days / 365.25
            return d.isoformat() if 10 <= age <= 120 else None
        except ValueError:
            pass
    return None


def normalize_phone(p: str):
    d = only_digits(p)
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    return d if len(d) in (10, 11) else None


def password_problem(pw: str):
    if not isinstance(pw, str) or len(pw) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if len(pw) > 128:
        return "Senha muito longa."
    return None


# ---------- rate limit simples (em memória) ----------
_FAILS: dict = {}
MAX_FAILS, WINDOW = 5, 15 * 60


def rate_key(identifier: str) -> str:
    return f"{request.remote_addr}|{identifier}"


def is_locked(key: str) -> bool:
    now = time.time()
    hits = [t for t in _FAILS.get(key, []) if now - t < WINDOW]
    _FAILS[key] = hits
    return len(hits) >= MAX_FAILS


def register_fail(key: str):
    _FAILS.setdefault(key, []).append(time.time())


def clear_fails(key: str):
    _FAILS.pop(key, None)
