# tests/conftest.py

# --- INÍCIO DA CORREÇÃO ---
import sys
import os
import pytest

# Adiciona o diretório raiz do projeto ao path do Python
# Isso permite que o pytest encontre o módulo 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --- FIM DA CORREÇÃO ---

from app import create_app, db

@pytest.fixture(scope='module')
def test_app():
    """
    Cria uma instância do aplicativo Flask configurada para teste.
    """
    app = create_app()
    app.config.from_object('app.config.Config')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Usa um banco de dados em memória
        "WTF_CSRF_ENABLED": False,  # Desabilita CSRF para facilitar os testes de formulário
        "LOGIN_DISABLED": False,
    })

    with app.app_context():
        db.create_all()
        yield app  # Fornece a instância do app para os testes
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """
    Cria um cliente de teste para simular requisições HTTP.
    """
    return test_app.test_client()