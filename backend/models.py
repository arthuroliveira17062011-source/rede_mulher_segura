import uuid
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, func # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore

from database import Base


class Usuaria(Base):
    __tablename__ = "usuaria"

    id_usuario = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    nome_completo = Column(String, nullable=False)
    cpf = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    telefone_celular = Column(String, nullable=False, unique=True)
    data_nascimento = Column(Date, nullable=False)
    endereco_residencia = Column(String, nullable=True)
    senha_hash = Column(String, nullable=False)
    frase_chave = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    contatos_emergencia = relationship(
        "ContatoEmergencia",
        back_populates="usuaria",
        cascade="all, delete-orphan"
    )


class ContatoEmergencia(Base):
    __tablename__ = "contato_emergencia"

    id_contato = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    id_usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("usuaria.id_usuario", ondelete="CASCADE"),
        nullable=False
    )
    nome_completo = Column(String, nullable=False)
    telefone_whatsapp = Column(String, nullable=False)
    prioridade_notificacao = Column(Integer, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    usuaria = relationship(
        "Usuaria",
        back_populates="contatos_emergencia"
    )