from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, status # type: ignore
from sqlalchemy.orm import Session # type: ignore

import models
import schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Rede Mulher Segura",
    version="1.0.0"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def inicio():
    return {"mensagem": "API Rede Mulher Segura operacional no Supabase"}


# ============================================================
# ROTAS DE USUÁRIA (ENTIDADE SIMPLES)
# ============================================================

@app.post(
    "/usuarias",
    response_model=schemas.UsuariaResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_usuaria(
    usuaria: schemas.UsuariaCreate,
    db: Session = Depends(get_db)
):
    cpf_existente = db.query(models.Usuaria).filter(models.Usuaria.cpf == usuaria.cpf).first()
    if cpf_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado"
        )

    nova_usuaria = models.Usuaria(**usuaria.model_dump())
    db.add(nova_usuaria)
    db.commit()
    db.refresh(nova_usuaria)

    return nova_usuaria


@app.get(
    "/usuarias",
    response_model=list[schemas.UsuariaResponse]
)
def listar_usuarias(
    db: Session = Depends(get_db)
):
    return db.query(models.Usuaria).all()


# ============================================================
# ROTAS DE CONTATO DE EMERGÊNCIA (ENTIDADE COM FK)
# ============================================================

@app.post(
    "/contatos-emergencia",
    response_model=schemas.ContatoEmergenciaResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_contato_emergencia(
    contato: schemas.ContatoEmergenciaCreate,
    db: Session = Depends(get_db)
):
    usuaria = db.query(models.Usuaria).filter(
        models.Usuaria.id_usuario == contato.id_usuario
    ).first()

    if usuaria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuária não encontrada"
        )

    novo_contato = models.ContatoEmergencia(
        id_usuario=contato.id_usuario,
        nome_completo=contato.nome_completo,
        telefone_whatsapp=contato.telefone_whatsapp,
        prioridade_notificacao=contato.prioridade_notificacao
    )

    db.add(novo_contato)
    db.commit()
    db.refresh(novo_contato)

    return {
        "id_contato": novo_contato.id_contato,
        "nome_completo": novo_contato.nome_completo,
        "telefone_whatsapp": novo_contato.telefone_whatsapp,
        "prioridade_notificacao": novo_contato.prioridade_notificacao,
        "usuaria": usuaria.nome_completo
    }


@app.get(
    "/contatos-emergencia",
    response_model=list[schemas.ContatoEmergenciaResponse]
)
def listar_contatos_emergencia(
    db: Session = Depends(get_db)
):
    contatos = db.query(models.ContatoEmergencia).all()

    return [
        {
            "id_contato": contato.id_contato,
            "nome_completo": contato.nome_completo,
            "telefone_whatsapp": contato.telefone_whatsapp,
            "prioridade_notificacao": contato.prioridade_notificacao,
            "usuaria": contato.usuaria.nome_completo
        }
        for contato in contatos
    ]