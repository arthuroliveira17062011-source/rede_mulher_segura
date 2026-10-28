import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import RequestError
from postgrest.exceptions import APIError
from controller import (
    usuarias,
    configuracoes_de_seguranca,
    contatos,
    ocorrencias_de_alerta,
    produtos,
    pedidos,
    itens_pedidos,
)

logger = logging.getLogger("uvicorn.error")
app = FastAPI(
    title="Rede Mulher Segura - API",
    description="CRUD com Supabase por HTTPS.",
)
app.include_router(usuarias.router)
app.include_router(configuracoes_de_seguranca.router)
app.include_router(contatos.router)
app.include_router(ocorrencias_de_alerta.router)
app.include_router(produtos.router)
app.include_router(pedidos.router)
app.include_router(itens_pedidos.router)

# Erros do Postgres que são culpa dos dados enviados, não do servidor.
# código -> (status HTTP, mensagem)
ERROS_DO_CLIENTE = {
    "23505": (409, "Já existe um registro com esses dados (valor duplicado)."),
    "23503": (409, "Referência inválida: o registro relacionado não existe "
                   "ou ainda está em uso."),
    "23502": (422, "Há um campo obrigatório ausente."),
    "23514": (422, "Algum valor enviado não é permitido."),
    "22P02": (422, "Algum valor enviado tem formato inválido."),
}


@app.exception_handler(APIError)
async def tratar_erro_supabase(request: Request, erro: APIError):
    logger.error("Erro na operação do Supabase: %s", erro)
    codigo = getattr(erro, "code", None)
    if codigo in ERROS_DO_CLIENTE:
        status_http, mensagem = ERROS_DO_CLIENTE[codigo]
        return JSONResponse(status_code=status_http,
                            content={"detail": mensagem})
    return JSONResponse(
        status_code=502,
        content={"detail": (
            "O Supabase recusou a operação. "
            "Confira a mensagem no terminal."
        )},
    )


@app.exception_handler(RequestError)
async def tratar_erro_rede(request: Request, erro: RequestError):
    logger.error("Falha de comunicação: %s", type(erro).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": (
            "Não foi possível acessar o Supabase. "
            "Verifique a conexão com a internet."
        )},
    )
