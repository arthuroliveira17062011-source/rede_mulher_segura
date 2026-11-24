import re
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


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
    # bcrypt só considera os 72 primeiros caracteres da senha.
    senha: str = Field(min_length=6, max_length=72)

    @field_validator("cpf")
    @classmethod
    def normalizar_cpf(cls, v: str) -> str:
        # Guarda só dígitos, para o login por CPF achar sempre o mesmo valor.
        digitos = re.sub(r"\D", "", v)
        if len(digitos) != 11:
            raise ValueError("CPF deve ter 11 dígitos.")
        return digitos

    @field_validator("telefone_celular")
    @classmethod
    def normalizar_telefone(cls, v: str) -> str:
        digitos = re.sub(r"\D", "", v)
        if not 10 <= len(digitos) <= 13:
            raise ValueError("Telefone deve ter DDD + número.")
        return digitos

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("E-mail inválido.")
        return v


class UsuariaSaida(UsuariaBase):
    """Resposta da API: nunca devolve senha nem frase_chave."""
    id_usuario: int
    criado_em: datetime


class UsuariaResumo(BaseModel):
    """Listagem pública: só o que a página de resumo precisa (sem CPF,
    telefone, e-mail ou endereço)."""
    id_usuario: int
    nome_completo: str
    criado_em: datetime


class LoginEntrada(BaseModel):
    login: str = Field(min_length=1)   # e-mail ou CPF
    senha: str = Field(min_length=1)


class SenhaAtualizacao(BaseModel):
    senha_atual: str = Field(min_length=1)               # confirma que é a dona da conta
    senha: str = Field(min_length=6, max_length=72)      # nova senha


class AreaRestritaSenha(BaseModel):
    """Senha da área restrita: a usuária escolhe o que quiser (letras, números, símbolos)."""
    senha: str = Field(min_length=4, max_length=72)
