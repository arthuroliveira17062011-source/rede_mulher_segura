from datetime import date, datetime
from pydantic import BaseModel, Field


class UsuariaBase(BaseModel):
    """Campos que podem ser devolvidos ao cliente."""
    nome_completo: str = Field(min_length=1)
    cpf: str = Field(min_length=1)
    email: str = Field(min_length=3)
    telefone_celular: str = Field(min_length=1)
    data_nascimento: date
    endereco_residencia: str | None = None


class UsuariaEntrada(UsuariaBase):
    """Dados recebidos no cadastro/atualização (com campos secretos)."""
    senha_hash: str = Field(min_length=1)
    frase_chave: str | None = None


class UsuariaSaida(UsuariaBase):
    """Resposta da API: nunca devolve senha_hash nem frase_chave."""
    id_usuario: int
    criado_em: datetime
