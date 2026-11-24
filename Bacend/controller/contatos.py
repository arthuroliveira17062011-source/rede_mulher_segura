from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.contatos import ContatoEntrada, ContatoSaida

router = APIRouter(
    prefix="/contatos",
    tags=["Contatos de emergência"],
)

@router.post("", response_model=ContatoSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_contato(dados: ContatoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("contatos_de_emergencia")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou o contato cadastrado.",
        )
    return resposta.data[0]

@router.get("", response_model=list[ContatoSaida])
def listar_contatos():
    resposta = (
        supabase.table("contatos_de_emergencia")
        .select("*")
        .order("id_contato")
        .execute()
    )
    return resposta.data

@router.get("/{id_contato}", response_model=ContatoSaida)
def consultar_contato(id_contato: UUID):
    resposta = (
        supabase.table("contatos_de_emergencia")
        .select("*")
        .eq("id_contato", str(id_contato))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Contato não encontrado.")
    return resposta.data[0]

@router.put("/{id_contato}", response_model=ContatoSaida)
def atualizar_contato(id_contato: UUID, dados: ContatoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("contatos_de_emergencia")
        .update(conteudo)
        .eq("id_contato", str(id_contato))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Contato não encontrado.")
    return resposta.data[0]

@router.delete("/{id_contato}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_contato(id_contato: UUID):
    resposta = (
        supabase.table("contatos_de_emergencia")
        .delete()
        .eq("id_contato", str(id_contato))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Contato não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
