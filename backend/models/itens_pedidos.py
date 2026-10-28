from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class ItemEntrada(BaseModel):
    id_pedido: UUID
    id_produto: UUID
    quantidade: int = Field(gt=0)
    preco_unit: Decimal = Field(ge=0)


class ItemSaida(ItemEntrada):
    id_item: UUID
