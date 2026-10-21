"""Envio de alertas aos contatos de confiança.

NOTIFY_MODE=log      -> apenas registra no log (padrão, bom para desenvolvimento)
NOTIFY_MODE=webhook  -> POST JSON em NOTIFY_WEBHOOK_URL (ligue a Twilio, Z-API,
                        Evolution API, n8n etc. sem mexer no resto do sistema)

Além disso sempre geramos links wa.me para o front abrir o WhatsApp com a
mensagem pronta (funciona sem nenhum provedor pago).
"""
import json
import logging
import os
import urllib.parse
import urllib.request

log = logging.getLogger("notifier")


def _wa_number(phone: str) -> str:
    return "55" + phone


def build_message(nome: str, lat, lng) -> str:
    base = f"🚨 ALERTA DE SOCORRO: {nome} precisa de ajuda agora."
    if lat is not None and lng is not None:
        base += f" Localização: https://maps.google.com/?q={lat},{lng}"
    else:
        base += " Localização indisponível — tente ligar para ela."
    return base


def notify_contacts(user_name: str, contacts: list, lat, lng) -> dict:
    msg = build_message(user_name, lat, lng)
    links = [
        {
            "nome": c["nome"],
            "url": f"https://wa.me/{_wa_number(c['telefone'])}?text={urllib.parse.quote(msg)}",
        }
        for c in contacts
    ]
    mode = os.environ.get("NOTIFY_MODE", "log")
    delivered = 0
    if mode == "webhook" and os.environ.get("NOTIFY_WEBHOOK_URL"):
        for c in contacts:
            body = json.dumps({"to": _wa_number(c["telefone"]), "name": c["nome"], "message": msg}).encode()
            req = urllib.request.Request(
                os.environ["NOTIFY_WEBHOOK_URL"], data=body, headers={"Content-Type": "application/json"}
            )
            try:
                urllib.request.urlopen(req, timeout=8).read()
                delivered += 1
            except Exception as exc:  # noqa: BLE001
                log.error("Falha ao notificar %s: %s", c["nome"], exc)
    else:
        for c in contacts:
            log.warning("[ALERTA] -> %s (%s): %s", c["nome"], c["telefone"], msg)
        delivered = len(contacts)
    return {"mensagem": msg, "entregues": delivered, "links": links}
