from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ContatoEntrada(BaseModel):
    id_usuario: UUID
    nome_completo: str = Field(min_length=1)
    telefone_whatsapp: str = Field(min_length=1)
    prioridade_notificacao: int = Field(ge=0)


class ContatoSaida(ContatoEntrada):
    id_contato: UUID
    criado_em: datetime
