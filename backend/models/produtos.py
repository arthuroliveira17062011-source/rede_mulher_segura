from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProdutoEntrada(BaseModel):
    nome: str = Field(min_length=1)
    descricao: str | None = None
    preco: Decimal = Field(ge=0)
    categoria: str = Field(min_length=1)
    url_imagem: str | None = None
    disponivel: bool | None = None


class ProdutoSaida(ProdutoEntrada):
    id_produto: UUID
    criado_em: datetime
