from uuid import UUID
from pydantic import BaseModel, Field


class ConfiguracaoBase(BaseModel):
    """Campos que podem ser devolvidos ao cliente."""
    id_usuario: UUID
    tempo_temporizador_segundo: int | None = Field(default=None, gt=0)
    tema_disfarce_padrao: str | None = None


class ConfiguracaoEntrada(ConfiguracaoBase):
    """Dados recebidos no cadastro/atualização (inclui o PIN)."""
    pin_desativado: str | None = None


class ConfiguracaoSaida(ConfiguracaoBase):
    """Resposta da API: nunca devolve o PIN de desativação."""
    id_configuracao: UUID
