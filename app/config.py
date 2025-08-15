# call_center_project/app/config.py

import os
# call_center_project/app/config.py

import os

class Config:
    # ... (suas configurações existentes como SECRET_KEY, etc.) ...
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave_secreta_padrao_para_desenvolvimento')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///avaliacoes_whatsapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Adicione esta linha para facilitar a troca para o modo de teste
    TESTING = False

# ... (outras classes de configuração se houver) ...

class Config:
    """Configurações base da aplicação."""
    # Chave secreta para proteger sessões e cookies.
    # Em produção, use um valor mais seguro e carregue de variáveis de ambiente.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave_secreta_padrao_para_desenvolvimento')

    # Configuração do banco de dados SQLite.
    # O banco será criado na pasta 'instance', que o Flask cria automaticamente.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///avaliacoes_whatsapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Tokens e Chaves de API ---
    # Token para proteger suas APIs internas
    API_TOKEN = "TOKEN_SUPER_SECRETO_CALL_CENTER_2024"

    # --- Configurações do WhatsApp Business API ---
    # !!! SUBSTITUA PELOS SEUS VALORES REAIS !!!
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', "SEU_TOKEN_WHATSAPP_BUSINESS_API")
    WHATSAPP_URL = os.environ.get('WHATSAPP_URL', "https://graph.facebook.com/v17.0/SEU_NUMERO_ID/messages" )
    WEBHOOK_VERIFY_TOKEN = os.environ.get('WEBHOOK_VERIFY_TOKEN', "SEU_TOKEN_WEBHOOK")
