# tests/conftest.py

import sys
import os
import pytest

# Adiciona o diretório raiz do projeto ao path do Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app, db

@pytest.fixture(scope='function') # <-- ALTERADO DE 'module' PARA 'function'
def test_app():
    """
    Cria uma instância do aplicativo Flask configurada para teste.
    """
    app = create_app()
    app.config.from_object('app.config.Config')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function') # <-- ALTERADO DE 'module' PARA 'function'
def test_client(test_app):
    """
    Cria um cliente de teste para simular requisições HTTP.
    """
    return test_app.test_client()