# call_center_project/app/services.py

import requests
from flask import current_app
from . import db
from .models import ConversaWhatsApp, MensagemWhatsApp, Email, Empresa

def enviar_mensagem_whatsapp(wa_id, mensagem):
    # ... (código existente)
    pass

def processar_mensagem_recebida(message):
    # ... (código existente)
    pass

# --- NOVA FUNÇÃO PARA ENVIAR EMAILS ---
def enviar_email_via_api(empresa: Empresa, destinatario: str, assunto: str, corpo_html: str):
    """
    Envia um email usando a chave de API e o remetente configurados pela empresa.
    Esta é uma função genérica. A implementação exata (URL, payload) dependerá
    do provedor de email escolhido (ex: SendGrid, Mailgun).
    
    Retorna True se o email foi enviado com sucesso, False caso contrário.
    """
    if not empresa.email_api_key or not empresa.email_sender:
        current_app.logger.error(f"Empresa {empresa.id} não possui credenciais de email configuradas.")
        return False

    # Exemplo genérico de como seria a chamada para uma API de email
    # NOTA: Substitua pela implementação real do seu provedor de email.
    api_url = "https://api.sendgrid.com/v3/mail/send" # Exemplo para SendGrid
    headers = {
        "Authorization": f"Bearer {empresa.email_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "personalizations": [{"to": [{"email": destinatario}]}],
        "from": {"email": empresa.email_sender, "name": current_app.config.get('MAIL_SENDER_NAME', 'Suporte')},
        "subject": assunto,
        "content": [{"type": "text/html", "value": corpo_html}]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Lança um erro para respostas 4xx ou 5xx
        
        # O SendGrid retorna 202 Accepted em caso de sucesso
        if response.status_code == 202:
            current_app.logger.info(f"Email para {destinatario} enviado com sucesso via API da empresa {empresa.id}.")
            return True
        else:
            current_app.logger.error(f"Erro ao enviar email para {destinatario} (Status: {response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Exceção ao tentar enviar email para {destinatario}: {e}")
        return False