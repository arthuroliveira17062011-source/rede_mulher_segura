import sqlite3
from flask import g, current_app # type: ignore

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  cpf TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  nascimento TEXT NOT NULL,
  celular TEXT NOT NULL,
  endereco TEXT NOT NULL,
  senha_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS menu_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  categoria TEXT NOT NULL,
  nome TEXT NOT NULL,
  descricao TEXT NOT NULL,
  preco_centavos INTEGER NOT NULL,
  ativo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mesa TEXT NOT NULL,
  total_centavos INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'recebido',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  menu_item_id INTEGER NOT NULL,
  nome TEXT NOT NULL,
  qtd INTEGER NOT NULL,
  preco_centavos INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  vinculo TEXT NOT NULL DEFAULT '',
  telefone TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lat REAL,
  lng REAL,
  contatos_notificados INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS evidences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  titulo TEXT NOT NULL,
  nota TEXT NOT NULL DEFAULT '',
  arquivo_nome TEXT,
  arquivo_mime TEXT,
  arquivo_tamanho INTEGER,
  arquivo_blob TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

MENU_SEED = [
    ("pf", "PF Bife a Cavalo", "Bife acebolado com 2 ovos fritos, arroz, feijão caseiro, farofa e salada da casa.", 2600),
    ("pf", "PF Frango Grelhado", "Filé de frango grelhado na chapa, arroz branco, feijão, purê de batata e salada.", 2200),
    ("marmitex", "Marmitex Comercial (M)", "Carne panela com batata, arroz, feijão e macarrão ao molho vermelho.", 1900),
    ("marmitex", "Marmitex Feijoada (G)", "Feijoada completa com couve refogada, farofa temperada, torresmo e laranjas.", 2800),
    ("salgados", "Coxinha de Frango c/ Catupiry", "Salgado frito na hora com recheio bem temperado de frango desfado.", 750),
    ("salgados", "Pastel de Carne Frito", "Pastel crocante recheado com carne moída temperada e azeitona.", 800),
    ("bebidas", "Suco de Laranja (500ml)", "Suco natural de laranja espremido na hora, gelado e sem açúcar.", 900),
    ("bebidas", "Refrigerante Lata (350ml)", "Coca-Cola, Guaraná Antarctica ou Fanta Laranja.", 600),
]


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO menu_items (categoria, nome, descricao, preco_centavos) VALUES (?,?,?,?)",
            MENU_SEED,
        )
    conn.commit()
    conn.close()
