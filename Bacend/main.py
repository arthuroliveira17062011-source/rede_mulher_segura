import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from httpx import RequestError
from postgrest.exceptions import APIError
from controller import (
    usuarias,
    configuracoes_de_seguranca,
    contatos,
    ocorrencias_de_alerta,
    pedidos,
)

logger = logging.getLogger("uvicorn.error")
app = FastAPI(
    title="Rede Mulher Segura - API",
    description="CRUD com Supabase por HTTPS.",
)

# CORS: permite que o frontend (porta 5500) leia as respostas da API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    # Também libera abrir o site pelo IP do computador na rede local
    # (ex.: http://192.168.0.10:5500 no celular), como o script.js prevê.
    allow_origin_regex=r"http://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):5500",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarias.router)
app.include_router(usuarias.router_login)
app.include_router(configuracoes_de_seguranca.router)
app.include_router(contatos.router)
app.include_router(ocorrencias_de_alerta.router)
app.include_router(pedidos.router)

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