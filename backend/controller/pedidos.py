from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.pedidos import PedidoEntrada, PedidoSaida

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"],
)

@router.post("", response_model=PedidoSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_pedido(dados: PedidoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("pedidos")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou o pedido cadastrado.",
        )
    return resposta.data[0]

@router.get("", response_model=list[PedidoSaida])
def listar_pedidos():
    resposta = (
        supabase.table("pedidos")
        .select("*")
        .order("id_pedido")
        .execute()
    )
    return resposta.data

@router.get("/{id_pedido}", response_model=PedidoSaida)
def consultar_pedido(id_pedido: UUID):
    resposta = (
        supabase.table("pedidos")
        .select("*")
        .eq("id_pedido", str(id_pedido))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Pedido não encontrado.")
    return resposta.data[0]

@router.put("/{id_pedido}", response_model=PedidoSaida)
def atualizar_pedido(id_pedido: UUID, dados: PedidoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("pedidos")
        .update(conteudo)
        .eq("id_pedido", str(id_pedido))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Pedido não encontrado.")
    return resposta.data[0]

@router.delete("/{id_pedido}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_pedido(id_pedido: UUID):
    resposta = (
        supabase.table("pedidos")
        .delete()
        .eq("id_pedido", str(id_pedido))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Pedido não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
