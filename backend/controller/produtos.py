from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.produtos import ProdutoEntrada, ProdutoSaida

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"],
)

@router.post("", response_model=ProdutoSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_produto(dados: ProdutoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("produtos")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou o produto cadastrado.",
        )
    return resposta.data[0]

@router.get("", response_model=list[ProdutoSaida])
def listar_produtos():
    resposta = (
        supabase.table("produtos")
        .select("*")
        .order("id_produto")
        .execute()
    )
    return resposta.data

@router.get("/{id_produto}", response_model=ProdutoSaida)
def consultar_produto(id_produto: UUID):
    resposta = (
        supabase.table("produtos")
        .select("*")
        .eq("id_produto", str(id_produto))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Produto não encontrado.")
    return resposta.data[0]

@router.put("/{id_produto}", response_model=ProdutoSaida)
def atualizar_produto(id_produto: UUID, dados: ProdutoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("produtos")
        .update(conteudo)
        .eq("id_produto", str(id_produto))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Produto não encontrado.")
    return resposta.data[0]

@router.delete("/{id_produto}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(id_produto: UUID):
    resposta = (
        supabase.table("produtos")
        .delete()
        .eq("id_produto", str(id_produto))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Produto não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
