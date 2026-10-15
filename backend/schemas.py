import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator  # type: ignore


def _digits(v: str) -> str:
    return re.sub(r"\D", "", v or "")


# --- SCHEMAS DE USUÁRIA ---
class UsuariaCreate(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=150)
    cpf: str
    email: EmailStr
    telefone_celular: str
    data_nascimento: date
    endereco_residencia: str | None = None
    senha: str = Field(min_length=8, max_length=128)  # texto puro; o servidor gera o hash
    frase_chave: str | None = None

    @field_validator("cpf")
    @classmethod
    def _cpf(cls, v: str) -> str:
        d = _digits(v)
        if len(d) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
        return d

    @field_validator("telefone_celular")
    @classmethod
    def _tel(cls, v: str) -> str:
        d = _digits(v)
        if d.startswith("55") and len(d) in (12, 13):
            d = d[2:]
        if len(d) not in (10, 11):
            raise ValueError("Telefone deve ter DDD + número")
        return d

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.lower()


class UsuariaResponse(BaseModel):
    id_usuario: UUID
    nome_completo: str
    email: str
    telefone_celular: str

    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DE CONTATO DE EMERGÊNCIA ---
class ContatoEmergenciaCreate(BaseModel):
    id_usuario: UUID
    nome_completo: str = Field(min_length=2, max_length=150)
    telefone_whatsapp: str
    prioridade_notificacao: int = Field(ge=1, le=10)

    @field_validator("telefone_whatsapp")
    @classmethod
    def _tel(cls, v: str) -> str:
        d = _digits(v)
        if d.startswith("55") and len(d) in (12, 13):
            d = d[2:]
        if len(d) not in (10, 11):
            raise ValueError("Telefone deve ter DDD + número")
        return d


class ContatoEmergenciaResponse(BaseModel):
    id_contato: UUID
    nome_completo: str
    telefone_whatsapp: str
    prioridade_notificacao: int
    usuaria: str

    model_config = ConfigDict(from_attributes=True)
