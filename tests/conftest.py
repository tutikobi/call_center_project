# tests/conftest.py

import sys
import os
import pytest

# Adiciona o diretório raiz do projeto ao path do Python
# Isto permite que o pytest encontre o módulo 'app'
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
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Usa um banco de dados em memória limpo para cada teste
        "WTF_CSRF_ENABLED": False,  # Desabilita CSRF para facilitar os testes de formulário
        "SECRET_KEY": "test-secret-key-for-sessions",
    })

    with app.app_context():
        db.create_all()
        yield app  # Fornece a instância da app para o teste
        db.drop_all() # Limpa a base de dados depois do teste

@pytest.fixture(scope='function')
def test_client(test_app):
    """
    Cria um cliente de teste para simular requisições HTTP para cada teste.
    """
    return test_app.test_client()