from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.usuarias import UsuariaEntrada, UsuariaSaida

router = APIRouter(
    prefix="/usuarias",
    tags=["Usuárias"],
)

@router.post("", response_model=UsuariaSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_usuaria(dados: UsuariaEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
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

@router.get("", response_model=list[UsuariaSaida])
def listar_usuarias():
    resposta = (
        supabase.table("usuaria")
        .select("*")
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

@router.put("/{id_usuario}", response_model=UsuariaSaida)
def atualizar_usuaria(id_usuario: int, dados: UsuariaEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("usuaria")
        .update(conteudo)
        .eq("id_usuario", id_usuario)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Usuária não encontrada.")
    return resposta.data[0]

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
