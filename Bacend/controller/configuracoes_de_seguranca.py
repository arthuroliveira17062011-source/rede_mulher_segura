from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.configuracoes_de_seguranca import (
    ConfiguracaoEntrada,
    ConfiguracaoSaida,
)

router = APIRouter(
    prefix="/configuracoes_de_seguranca",
    tags=["Configurações de segurança"],
)

@router.post("", response_model=ConfiguracaoSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_configuracao(dados: ConfiguracaoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("configuracoes_de_seguranca")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou a configuração cadastrada.",
        )
    return resposta.data[0]

@router.get("", response_model=list[ConfiguracaoSaida])
def listar_configuracoes():
    resposta = (
        supabase.table("configuracoes_de_seguranca")
        .select("*")
        .order("id_configuracao")
        .execute()
    )
    return resposta.data

@router.get("/{id_configuracao}", response_model=ConfiguracaoSaida)
def consultar_configuracao(id_configuracao: UUID):
    resposta = (
        supabase.table("configuracoes_de_seguranca")
        .select("*")
        .eq("id_configuracao", str(id_configuracao))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Configuração não encontrada.")
    return resposta.data[0]

@router.put("/{id_configuracao}", response_model=ConfiguracaoSaida)
def atualizar_configuracao(id_configuracao: UUID, dados: ConfiguracaoEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("configuracoes_de_seguranca")
        .update(conteudo)
        .eq("id_configuracao", str(id_configuracao))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Configuração não encontrada.")
    return resposta.data[0]

@router.delete("/{id_configuracao}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_configuracao(id_configuracao: UUID):
    resposta = (
        supabase.table("configuracoes_de_seguranca")
        .delete()
        .eq("id_configuracao", str(id_configuracao))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Configuração não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
