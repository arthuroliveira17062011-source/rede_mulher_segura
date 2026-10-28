from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.itens_pedidos import ItemEntrada, ItemSaida

router = APIRouter(
    prefix="/itens_pedidos",
    tags=["Itens de pedidos"],
)

@router.post("", response_model=ItemSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_item(dados: ItemEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("itens_pedidos")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou o item cadastrado.",
        )
    return resposta.data[0]

@router.get("", response_model=list[ItemSaida])
def listar_itens():
    resposta = (
        supabase.table("itens_pedidos")
        .select("*")
        .order("id_item")
        .execute()
    )
    return resposta.data

@router.get("/{id_item}", response_model=ItemSaida)
def consultar_item(id_item: UUID):
    resposta = (
        supabase.table("itens_pedidos")
        .select("*")
        .eq("id_item", str(id_item))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Item não encontrado.")
    return resposta.data[0]

@router.put("/{id_item}", response_model=ItemSaida)
def atualizar_item(id_item: UUID, dados: ItemEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("itens_pedidos")
        .update(conteudo)
        .eq("id_item", str(id_item))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Item não encontrado.")
    return resposta.data[0]

@router.delete("/{id_item}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(id_item: UUID):
    resposta = (
        supabase.table("itens_pedidos")
        .delete()
        .eq("id_item", str(id_item))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Item não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
