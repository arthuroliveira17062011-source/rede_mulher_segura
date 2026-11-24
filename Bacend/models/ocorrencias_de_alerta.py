from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class AlertaEntrada(BaseModel):
    id_usuario: int   # usuaria.id_usuario é inteiro (não UUID)
    # O frontend não envia a data; se faltar, o controller usa "agora" (UTC).
    data_hora_ativacao: datetime | None = None
    tipo_ativacao: str = Field(min_length=1)
    link_google_maps_localizacao: str | None = None
    link_compartilhamento: str | None = None


class AlertaSaida(AlertaEntrada):
    id_alerta: UUID
    data_hora_ativacao: datetime
