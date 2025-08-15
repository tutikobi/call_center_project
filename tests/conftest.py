# tests/conftest.py

import sys
import os
import pytest

# Adiciona o diretório raiz do projeto (onde este ficheiro está) ao path do Python
# Isto permite que o pytest encontre o módulo 'app' que é seu vizinho
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app, db

@pytest.fixture(scope='function')
def test_app():
    """
    Cria uma instância da aplicação Flask para cada teste, garantindo isolamento total.
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key-for-sessions",
        "LOGIN_DISABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def test_client(test_app):
    """
    Cria um cliente de teste para simular requisições HTTP.
    """
    return test_app.test_client()