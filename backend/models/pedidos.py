from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PedidoEntrada(BaseModel):
    id_usuario: UUID | None = None
    valor_total: Decimal = Field(ge=0)
    status: str | None = None


class PedidoSaida(PedidoEntrada):
    id_pedido: UUID
    criado_em: datetime
