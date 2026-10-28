from uuid import UUID
from fastapi import APIRouter, HTTPException, Response, status
from database import supabase
from models.ocorrencias_de_alerta import AlertaEntrada, AlertaSaida

router = APIRouter(
    prefix="/ocorrencias_de_alerta",
    tags=["Ocorrências de alerta"],
)

@router.post("", response_model=AlertaSaida,
             status_code=status.HTTP_201_CREATED)
def cadastrar_alerta(dados: AlertaEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("ocorrencias_de_alerta")
        .insert(conteudo)
        .execute()
    )
    if not resposta.data:
        raise HTTPException(
            status_code=502,
            detail="O Supabase não retornou a ocorrência cadastrada.",
        )
    return resposta.data[0]

@router.get("", response_model=list[AlertaSaida])
def listar_alertas():
    resposta = (
        supabase.table("ocorrencias_de_alerta")
        .select("*")
        .order("id_alerta")
        .execute()
    )
    return resposta.data

@router.get("/{id_alerta}", response_model=AlertaSaida)
def consultar_alerta(id_alerta: UUID):
    resposta = (
        supabase.table("ocorrencias_de_alerta")
        .select("*")
        .eq("id_alerta", str(id_alerta))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Ocorrência não encontrada.")
    return resposta.data[0]

@router.put("/{id_alerta}", response_model=AlertaSaida)
def atualizar_alerta(id_alerta: UUID, dados: AlertaEntrada):
    conteudo = dados.model_dump(mode="json", exclude_unset=True)
    resposta = (
        supabase.table("ocorrencias_de_alerta")
        .update(conteudo)
        .eq("id_alerta", str(id_alerta))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Ocorrência não encontrada.")
    return resposta.data[0]

@router.delete("/{id_alerta}",
               status_code=status.HTTP_204_NO_CONTENT)
def excluir_alerta(id_alerta: UUID):
    resposta = (
        supabase.table("ocorrencias_de_alerta")
        .delete()
        .eq("id_alerta", str(id_alerta))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(404, "Ocorrência não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
