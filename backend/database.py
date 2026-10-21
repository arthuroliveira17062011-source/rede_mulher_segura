import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.engine import make_url  # type: ignore
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore

load_dotenv()

log = logging.getLogger("database")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi definida no arquivo .env")

# O driver instalado é o psycopg 3 ("psycopg"). Normaliza qualquer prefixo
# que o Supabase/Heroku/etc. entregue para o dialeto correto do SQLAlchemy.
for prefix in ("postgres://", "postgresql://", "postgresql+psycopg2://"):
    if DATABASE_URL.startswith(prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefix):]
        break

url = make_url(DATABASE_URL)
is_postgres = url.get_backend_name() == "postgresql"
host = url.host or ""

connect_args: dict = {}
engine_kwargs: dict = {}

if is_postgres:
    # Supabase exige SSL.
    connect_args["sslmode"] = "require"
    connect_args["connect_timeout"] = 10

    # Modo "transaction" do pooler (porta 6543) não suporta prepared statements.
    if url.port == 6543:
        connect_args["prepare_threshold"] = None

    engine_kwargs.update(
        pool_pre_ping=True,   # descarta conexões mortas antes de usar
        pool_recycle=300,     # recicla conexões a cada 5 min (pooler fecha ociosas)
        pool_size=5,
        max_overflow=5,
    )

    # Avisos para os dois erros mais comuns com Supabase
    if host.startswith("db.") and host.endswith(".supabase.co"):
        log.warning(
            "DATABASE_URL usa a conexão DIRETA (%s). Ela só funciona via IPv6. "
            "Se sua rede/servidor não tem IPv6, use o 'Session pooler' "
            "(aws-0-<regiao>.pooler.supabase.com) no lugar.", host
        )
    if "pooler.supabase.com" in host and "." not in (url.username or ""):
        log.warning(
            "No pooler do Supabase o usuário precisa ser 'postgres.<project-ref>' "
            "e não apenas '%s'.", url.username
        )
elif url.get_backend_name() == "sqlite":
    connect_args["check_same_thread"] = False

engine = create_engine(url, connect_args=connect_args, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
