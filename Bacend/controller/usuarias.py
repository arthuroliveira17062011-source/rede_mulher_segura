import re

from fastapi import APIRouter, HTTPException, Response, status
from passlib.context import CryptContext

from database import supabase
from models.contatos import ContatoSaida
from models.usuarias import (
    AreaRestritaSenha,
    LoginEntrada,
    SenhaAtualizacao,
    UsuariaEntrada,
    UsuariaResumo,
    UsuariaSaida,
)

router = APIRouter(
    prefix="/usuarias",
    tags=["Usuárias"],
)

# Rota de login fica fora do prefixo /usuarias (o frontend chama POST /login).
router_login = APIRouter(tags=["Autenticação"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash "de mentira" para gastar o mesmo tempo quando o login não existe
# (evita descobrir quais e-mails/CPFs estão cadastrados pelo tempo de resposta).
_HASH_FALSO = pwd_context.hash("senha-falsa-para-igualar-tempo")


def preparar_conteudo(dados: UsuariaEntrada) -> dict:
    """Converte os dados recebidos no formato da tabela:
    remove a 'senha' pura e coloca o 'senha_hash' no lugar."""
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    senha = conteudo.pop("senha")
    conteudo["senha_hash"] = pwd_context.hash(senha)
    return conteudo


# ------------------------------------------------------------------- login
@router_login.post("/login", response_model=UsuariaSaida)
def entrar(dados: LoginEntrada):
    """Autentica por e-mail ou CPF. Devolve a usuária (sem senha)."""
    login = dados.login.strip()
    if "@" in login:
        coluna, valor = "email", login.lower()
    else:
        coluna, valor = "cpf", re.sub(r"\D", "", login)

    resposta = (
        supabase.table("usuaria")
        .select("*")
        .eq(coluna, valor)
        .limit(1)
        .execute()
    )
    usuaria = resposta.data[0] if resposta.data else None
    hash_salvo = (usuaria or {}).get("senha_hash") or _HASH_FALSO

    senha_ok = pwd_context.verify(dados.senha, hash_salvo)
    # Mesma mensagem para "não existe" e "senha errada".
    if not usuaria or not senha_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF/e-mail ou senha incorretos.",
        )
    return usuaria


# ---------------------------------------------------------------- usuárias
@router.post("", response_model=UsuariaSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_usuaria(dados: UsuariaEntrada):
    conteudo = preparar_conteudo(dados)
    resposta = (
        supabase.table("usuaria")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou a usuária cadastrada.",
        )
    return resposta.data[0]


@router.get("", response_model=list[UsuariaResumo])
def listar_usuarias():
    """Lista pública e enxuta (usada por pages/resumo.html).
    Não devolve CPF, telefone, e-mail nem endereço."""
    resposta = (
        supabase.table("usuaria")
        .select("id_usuario, nome_completo, criado_em")
        .order("id_usuario")
        .execute()
    )
    return resposta.data


@router.get("/{id_usuario}", response_model=UsuariaSaida)
def consultar_usuaria(id_usuario: int):
    resposta = (
        supabase.table("usuaria")
        .select("*")
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return resposta.data[0]


@router.get("/{id_usuario}/contatos", response_model=list[ContatoSaida])
def listar_contatos_da_usuaria(id_usuario: int):
    """Contatos de emergência SÓ desta usuária, por ordem de prioridade."""
    resposta = (
        supabase.table("contatos_de_emergencia")
        .select("*")
        .eq("id_usuario", id_usuario)
        .order("prioridade_notificacao")
        .execute()
    )
    return resposta.data


@router.put("/{id_usuario}", response_model=UsuariaSaida)
def atualizar_usuaria(id_usuario: int, dados: UsuariaEntrada):
    conteudo = preparar_conteudo(dados)
    resposta = (
        supabase.table("usuaria")
        .update(conteudo)
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return resposta.data[0]


@router.patch("/{id_usuario}", response_model=UsuariaSaida)
def atualizar_senha(id_usuario: int, dados: SenhaAtualizacao):
    """Troca só a senha (o frontend envia PATCH {senha_atual, senha})."""
    atual = (
        supabase.table("usuaria")
        .select("senha_hash")
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not atual.data:
        raise HTTPException(404, "Usuária não encontrada.")
    if not pwd_context.verify(dados.senha_atual, atual.data[0]["senha_hash"]):
        raise HTTPException(403, "Senha atual incorreta.")
    resposta = (
        supabase.table("usuaria")
        .update({"senha_hash": pwd_context.hash(dados.senha)})
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return resposta.data[0]


# ----------------------------------------------- senha da área restrita
def _hash_area_restrita(id_usuario: int):
    """Devolve o hash salvo (ou None se ainda não foi definida). 404 se a usuária não existe."""
    r = (
        supabase.table("usuaria")
        .select("senha_area_restrita_hash")
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not r.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return r.data[0].get("senha_area_restrita_hash")


@router.get("/{id_usuario}/area-restrita")
def status_area_restrita(id_usuario: int):
    """O frontend usa isto para saber se mostra 'criar senha' (1º acesso) ou 'entrar'."""
    return {"definida": bool(_hash_area_restrita(id_usuario))}


@router.put("/{id_usuario}/area-restrita", status_code=status.HTTP_204_NO_CONTENT)
def definir_senha_area_restrita(id_usuario: int, dados: AreaRestritaSenha):
    """Primeiro acesso: define a senha. Só funciona se ainda não houver uma."""
    if _hash_area_restrita(id_usuario):
        raise HTTPException(409, "A senha da área restrita já foi definida.")
    resposta = (
        supabase.table("usuaria")
        .update({"senha_area_restrita_hash": pwd_context.hash(dados.senha)})
        .eq("id_usuario", id_usuario)
        .is_("senha_area_restrita_hash", "null")   # não sobrescreve se alguém definiu agora
        .execute()
    )
    if not resposta.data:
        raise HTTPException(409, "A senha da área restrita já foi definida.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id_usuario}/area-restrita/verificar", status_code=status.HTTP_204_NO_CONTENT)
def verificar_senha_area_restrita(id_usuario: int, dados: AreaRestritaSenha):
    hash_salvo = _hash_area_restrita(id_usuario)
    if not hash_salvo:
        raise HTTPException(409, "A senha da área restrita ainda não foi definida.")
    if not pwd_context.verify(dados.senha, hash_salvo):
        raise HTTPException(401, "Senha incorreta.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{id_usuario}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuaria(id_usuario: int):
    resposta = (
        supabase.table("usuaria")
        .delete()
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
