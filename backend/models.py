import uuid
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Uuid, CheckConstraint, func # type: ignore
from sqlalchemy.orm import relationship # type: ignore

from database import Base


class Usuaria(Base):
    __tablename__ = "usuaria"

    id_usuario = Column(
        Uuid(as_uuid=True),
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
    ocorrencias = relationship(
        "OcorrenciaDeAlerta",
        back_populates="usuaria",
        cascade="all, delete-orphan"
    )
    configuracao = relationship(
        "ConfiguracaoDeSeguranca",
        back_populates="usuaria",
        cascade="all, delete-orphan",
        uselist=False
    )


class ContatoEmergencia(Base):
    __tablename__ = "contato_emergencia"

    id_contato = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    id_usuario = Column(
        Uuid(as_uuid=True),
        ForeignKey("usuaria.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    nome_completo = Column(String, nullable=False)
    telefone_whatsapp = Column(String, nullable=False)
    prioridade_notificacao = Column(Integer, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    usuaria = relationship(
        "Usuaria",
        back_populates="contatos_emergencia"
    )


class OcorrenciaDeAlerta(Base):
    __tablename__ = "ocorrencias_de_alerta"
    __table_args__ = (
        CheckConstraint(
            "tipo_ativacao in ('botao', 'comando_voz', 'temporizador')",
            name="ck_ocorrencia_tipo_ativacao",
        ),
    )

    id_alerta = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    id_usuario = Column(
        Uuid(as_uuid=True),
        ForeignKey("usuaria.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    data_hora_ativacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tipo_ativacao = Column(String, nullable=False)
    link_google_maps_localizacao = Column(String, nullable=True)
    link_compartilhamento = Column(String, nullable=True)

    usuaria = relationship("Usuaria", back_populates="ocorrencias")


class ConfiguracaoDeSeguranca(Base):
    __tablename__ = "configuracoes_de_seguranca"

    id_configuracao = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    id_usuario = Column(
        Uuid(as_uuid=True),
        ForeignKey("usuaria.id_usuario", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    tempo_temporizador_segundo = Column(Integer, nullable=True)
    pin_desativado = Column(String, nullable=True)  # guarda o HASH do PIN, nunca o PIN
    tema_disfarce_padrao = Column(String, default="cardapio_restaurante")

    usuaria = relationship("Usuaria", back_populates="configuracao")
