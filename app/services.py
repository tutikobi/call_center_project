# call_center_project/app/services.py

import requests
from flask import current_app
from . import db
from .models import ConversaWhatsApp, MensagemWhatsApp

def enviar_mensagem_whatsapp(wa_id, mensagem):
    """Envia uma mensagem de texto via WhatsApp Business API."""
    headers = {
        "Authorization": f"Bearer {current_app.config['WHATSAPP_TOKEN']}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "text",
        "text": {"body": mensagem}
    }
    
    try:
        response = requests.post(current_app.config['WHATSAPP_URL'], headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao enviar mensagem para o WhatsApp: {e}")
        return None

def processar_mensagem_recebida(message):
    """Processa uma mensagem recebida do webhook do WhatsApp."""
    wa_id = message["from"]
    conteudo = message.get("text", {}).get("body", "Mídia não suportada")

    conversa = ConversaWhatsApp.query.filter_by(wa_id=wa_id, status='ativo').first()
    
    if not conversa:
        conversa = ConversaWhatsApp(
            wa_id=wa_id,
            nome_cliente=f"Cliente {wa_id[-4:]}",
            status='ativo'
        )
        db.session.add(conversa)
        db.session.flush()

    nova_mensagem = MensagemWhatsApp(
        conversa_id=conversa.id,
        remetente='cliente',
        conteudo=conteudo
    )
    db.session.add(nova_mensagem)
    db.session.commit()
    
    current_app.logger.info(f"Nova mensagem recebida na conversa {conversa.id} do cliente {wa_id}")
