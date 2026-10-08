# Restaurante Sabor Caseiro + Rede Mulher Segura — Backend

Backend em **Python/Flask + SQLite** para o front (`index.html` / `style.css`) enviado.
A tela pública é o restaurante (cardápio e comanda reais); a **Área Restrita** é o app de
proteção à mulher, com alerta de emergência, cofre de evidências, assistente local e contatos.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # opcional; as chaves são geradas sozinhas em data/
python app.py                    # http://127.0.0.1:5000
```

Testes: `python -m unittest discover -s tests -v`

Produção: `gunicorn -w 2 -b 127.0.0.1:8000 "app:create_app()"` atrás de um proxy com HTTPS
(defina `SECURE_HEADERS_HSTS=1`).

## Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Rotas da API e servidor do front |
| `db.py` | Schema SQLite e seed do cardápio |
| `security.py` | Hash de senha, JWT, validação de CPF/telefone, limite de tentativas |
| `notifier.py` | Envio do alerta (log, webhook e links WhatsApp) |
| `rag.py` + `data/knowledge.json` | Assistente local (busca por palavras-chave, sem IA externa) |
| `public/` | `index.html`, `style.css` (+ adições) e `app.js` (novo, liga o front à API) |

## API

Públicas: `GET /api/menu`, `POST /api/orders`, `POST /api/auth/register`, `POST /api/auth/login`.

Autenticadas (`Authorization: Bearer <token>`):

- `GET /api/me`, `POST /api/me/password`, `DELETE /api/me` (apaga conta e dados)
- `GET|POST /api/contacts`, `DELETE /api/contacts/<id>`
- `POST /api/alerts` (`{lat, lng}`), `GET /api/alerts`
- `GET|POST /api/evidences` (multipart), `GET /api/evidences/<id>/download`, `DELETE /api/evidences/<id>`
- `POST /api/rag` (`{pergunta}`)

## Segurança implementada

- Senhas com scrypt; JWT de 8h; token em `sessionStorage` (some ao fechar a aba)
- Bloqueio após 5 tentativas de login falhas (15 min); mensagens de erro genéricas
- Arquivos do Cofre **criptografados em repouso** (Fernet); cada usuária só acessa os seus
- Preço do pedido calculado no servidor; consultas SQL parametrizadas; front sem `innerHTML`
- CSP, `X-Frame-Options`, `no-store` na API; `ESC` na área restrita volta ao restaurante
- Assistente RAG e alertas não enviam dados a terceiros (exceto o webhook que você configurar)

## O que você precisa ajustar antes de usar de verdade

1. **Alertas reais**: por padrão só há log + links `wa.me` que abrem o WhatsApp da usuária.
   Para disparo automático, use `NOTIFY_MODE=webhook` e `NOTIFY_WEBHOOK_URL` (Twilio, Z-API,
   Evolution API, n8n...). Recebe `{to, name, message}`.
2. **Base do assistente**: edite `data/knowledge.json` com endereços, telefones e horários
   *confirmados* da DEAM, CRAS/CREAS e demais serviços de Maringá. O conteúdo legal incluso é
   geral — revise com uma profissional jurídica.
3. **Backup**: faça backup de `data/` inteiro (banco + `vault/` + `.evidence.key`). Sem a chave,
   os arquivos do Cofre não podem ser recuperados.
4. **LGPD**: o sistema guarda dados sensíveis; publique política de privacidade e restrinja o
   acesso ao servidor.
5. O SQLite não é criptografado — proteja o disco do servidor (criptografia de disco).
