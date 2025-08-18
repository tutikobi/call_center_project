# call_center_project/app/config.py

import os

class Config:
    """Configurações base da aplicação."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave_secreta_padrao_para_desenvolvimento')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://postgres:2509@localhost:5432/call_center_db'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    TESTING = False

    # --- NOVO CAMPO ADICIONADO ---
    # Chave para a API do Google Places. Será obtida no Google Cloud Console.
    GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'SUA_CHAVE_API_AQUI')

    # --- Tokens e Chaves de API ---
    API_TOKEN = "TOKEN_SUPER_SECRETO_CALL_CENTER_2024"

    # --- Configurações do WhatsApp Business API ---
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', "SEU_TOKEN_WHATSAPP_BUSINESS_API")
    WHATSAPP_URL = os.environ.get('WHATSAPP_URL', "https://graph.facebook.com/v17.0/SEU_NUMERO_ID/messages" )
    WEBHOOK_VERIFY_TOKEN = os.environ.get('WEBHOOK_VERIFY_TOKEN', "SEU_TOKEN_WEBHOOK")