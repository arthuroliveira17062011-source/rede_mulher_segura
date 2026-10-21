import logging
import os
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy import text  # type: ignore
from sqlalchemy.exc import IntegrityError, OperationalError  # type: ignore
from sqlalchemy.orm import Session, joinedload  # type: ignore

import models
import schemas
from database import SessionLocal, engine
from passwords import hash_password

log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Criar as tabelas AQUI (e não na importação) evita que o servidor
    # inteiro caia se o banco estiver fora do ar na hora de subir.
    try:
        models.Base.metadata.create_all(bind=engine)
        log.info("Banco conectado e tabelas verificadas.")
    except OperationalError as exc:
        log.error("Não foi possível conectar ao banco na inicialização: %s", exc.orig)
    yield


app = FastAPI(
    title="api projeto integrador",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OperationalError)
async def db_indisponivel(_req: Request, exc: OperationalError):
    log.error("Erro de conexão com o banco: %s", exc.orig)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Banco de dados indisponível. Tente novamente em instantes."},
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def inicio():
    return {"mensagem": "api projeto integrador operacional no Supabase"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Testa a conexão com o banco (útil para diagnosticar o Supabase)."""
    db.execute(text("SELECT 1"))
    return {"banco": "ok"}


# ============================================================
# ROTAS DE USUÁRIA
# ============================================================

@app.post(
    "/usuarias",
    response_model=schemas.UsuariaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_usuaria(usuaria: schemas.UsuariaCreate, db: Session = Depends(get_db)):
    existente = (
        db.query(models.Usuaria)
        .filter(
            (models.Usuaria.cpf == usuaria.cpf)
            | (models.Usuaria.email == usuaria.email)
            | (models.Usuaria.telefone_celular == usuaria.telefone_celular)
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe cadastro com este CPF, e-mail ou telefone",
        )

    dados = usuaria.model_dump(exclude={"senha"})
    nova = models.Usuaria(**dados, senha_hash=hash_password(usuaria.senha))
    db.add(nova)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe cadastro com este CPF, e-mail ou telefone",
        )
    db.refresh(nova)
    return nova


@app.get("/usuarias", response_model=list[schemas.UsuariaResponse])
def listar_usuarias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    return (
        db.query(models.Usuaria)
        .order_by(models.Usuaria.criado_em)
        .offset(max(skip, 0))
        .limit(limit)
        .all()
    )


# ============================================================
# ROTAS DE CONTATO DE EMERGÊNCIA
# ============================================================

def _contato_json(contato: models.ContatoEmergencia, nome_usuaria: str) -> dict:
    return {
        "id_contato": contato.id_contato,
        "nome_completo": contato.nome_completo,
        "telefone_whatsapp": contato.telefone_whatsapp,
        "prioridade_notificacao": contato.prioridade_notificacao,
        "usuaria": nome_usuaria,
    }


@app.post(
    "/contatos-emergencia",
    response_model=schemas.ContatoEmergenciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_contato_emergencia(
    contato: schemas.ContatoEmergenciaCreate, db: Session = Depends(get_db)
):
    usuaria = (
        db.query(models.Usuaria)
        .filter(models.Usuaria.id_usuario == contato.id_usuario)
        .first()
    )
    if usuaria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuária não encontrada"
        )

    novo = models.ContatoEmergencia(**contato.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return _contato_json(novo, usuaria.nome_completo)


@app.get(
    "/contatos-emergencia",
    response_model=list[schemas.ContatoEmergenciaResponse],
)
def listar_contatos_emergencia(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    limit = max(1, min(limit, 500))
    contatos = (
        db.query(models.ContatoEmergencia)
        .options(joinedload(models.ContatoEmergencia.usuaria))  # evita N+1 queries
        .order_by(models.ContatoEmergencia.prioridade_notificacao)
        .offset(max(skip, 0))
        .limit(limit)
        .all()
    )
    return [_contato_json(c, c.usuaria.nome_completo) for c in contatos]


# ============================================================
# ROTAS DE OCORRÊNCIAS DE ALERTA
# ============================================================

def _buscar_usuaria_ou_404(db: Session, id_usuario) -> models.Usuaria:
    usuaria = (
        db.query(models.Usuaria)
        .filter(models.Usuaria.id_usuario == id_usuario)
        .first()
    )
    if usuaria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuária não encontrada"
        )
    return usuaria


@app.post(
    "/alertas",
    response_model=schemas.OcorrenciaAlertaResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_alerta(
    alerta: schemas.OcorrenciaAlertaCreate, db: Session = Depends(get_db)
):
    _buscar_usuaria_ou_404(db, alerta.id_usuario)

    novo = models.OcorrenciaDeAlerta(**alerta.model_dump(mode="python"))
    novo.tipo_ativacao = alerta.tipo_ativacao.value
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get(
    "/usuarias/{id_usuario}/alertas",
    response_model=list[schemas.OcorrenciaAlertaResponse],
)
def listar_alertas_da_usuaria(
    id_usuario: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    _buscar_usuaria_ou_404(db, id_usuario)
    limit = max(1, min(limit, 500))
    return (
        db.query(models.OcorrenciaDeAlerta)
        .filter(models.OcorrenciaDeAlerta.id_usuario == id_usuario)
        .order_by(models.OcorrenciaDeAlerta.data_hora_ativacao.desc())
        .offset(max(skip, 0))
        .limit(limit)
        .all()
    )


# ============================================================
# ROTAS DE CONFIGURAÇÕES DE SEGURANÇA
# ============================================================

def _configuracao_json(cfg: models.ConfiguracaoDeSeguranca) -> dict:
    return {
        "id_configuracao": cfg.id_configuracao,
        "tempo_temporizador_segundo": cfg.tempo_temporizador_segundo,
        "tema_disfarce_padrao": cfg.tema_disfarce_padrao,
        "possui_pin": bool(cfg.pin_desativado),
    }


def _configuracao_da_usuaria(db: Session, id_usuario) -> models.ConfiguracaoDeSeguranca | None:
    return (
        db.query(models.ConfiguracaoDeSeguranca)
        .filter(models.ConfiguracaoDeSeguranca.id_usuario == id_usuario)
        .first()
    )


@app.post(
    "/configuracoes-seguranca",
    response_model=schemas.ConfiguracaoSegurancaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_configuracao(
    cfg: schemas.ConfiguracaoSegurancaCreate, db: Session = Depends(get_db)
):
    _buscar_usuaria_ou_404(db, cfg.id_usuario)
    if _configuracao_da_usuaria(db, cfg.id_usuario) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta usuária já possui configurações. Use PATCH para alterar.",
        )

    dados = cfg.model_dump(exclude={"pin_desativado"})
    nova = models.ConfiguracaoDeSeguranca(
        **dados,
        pin_desativado=hash_password(cfg.pin_desativado) if cfg.pin_desativado else None,
    )
    db.add(nova)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta usuária já possui configurações.",
        )
    db.refresh(nova)
    return _configuracao_json(nova)


@app.get(
    "/usuarias/{id_usuario}/configuracoes-seguranca",
    response_model=schemas.ConfiguracaoSegurancaResponse,
)
def obter_configuracao(id_usuario: UUID, db: Session = Depends(get_db)):
    cfg = _configuracao_da_usuaria(db, id_usuario)
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurações não encontradas",
        )
    return _configuracao_json(cfg)


@app.patch(
    "/usuarias/{id_usuario}/configuracoes-seguranca",
    response_model=schemas.ConfiguracaoSegurancaResponse,
)
def atualizar_configuracao(
    id_usuario: UUID,
    dados: schemas.ConfiguracaoSegurancaUpdate,
    db: Session = Depends(get_db),
):
    cfg = _configuracao_da_usuaria(db, id_usuario)
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurações não encontradas",
        )

    alteracoes = dados.model_dump(exclude_unset=True)
    if "pin_desativado" in alteracoes:
        pin = alteracoes.pop("pin_desativado")
        cfg.pin_desativado = hash_password(pin) if pin else None
    for campo, valor in alteracoes.items():
        setattr(cfg, campo, valor)

    db.commit()
    db.refresh(cfg)
    return _configuracao_json(cfg)
