# tests/test_authentication.py

from app.models import Usuario, Empresa
from app import db

def test_agent_login_and_logout(test_client):
    """Testa o fluxo de login e logout para um utilizador 'agente'."""
    # Configuração
    empresa = Empresa(nome_empresa="Empresa Agente", cnpj="11.111.111/0001-11")
    db.session.add(empresa)
    db.session.commit()
    user = Usuario(email="agent@test.com", nome="Test Agent", empresa_id=empresa.id, role="agente")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Teste de Login
    response = test_client.post('/login', data={'email': 'agent@test.com', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard Unificado" in response.data
    assert b"Login" not in response.data

    # Teste de Logout
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_superadmin_login(test_client):
    """Testa o fluxo de login para um utilizador 'super_admin'."""
    # Configuração
    empresa_admin = Empresa(nome_empresa="Sistema Call Center", cnpj="00.000.000/0001-00")
    db.session.add(empresa_admin)
    db.session.commit()
    super_admin = Usuario(email="super@admin.com", nome="Super Admin", empresa_id=empresa_admin.id, role="super_admin")
    super_admin.set_password("superpassword")
    db.session.add(super_admin)
    db.session.commit()

    # Teste de Login
    response = test_client.post('/login', data={'email': 'super@admin.com', 'password': 'superpassword'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard do Administrador" in response.data

def test_login_with_wrong_password(test_client):
    """Testa a falha de login com palavra-passe incorreta."""
    # Configuração
    empresa = Empresa(nome_empresa="Empresa Teste", cnpj="33.333.333/0001-33")
    db.session.add(empresa)
    db.session.commit()
    user = Usuario(email="user@test.com", nome="Test User", empresa_id=empresa.id, role="agente")
    user.set_password("correctpassword")
    db.session.add(user)
    db.session.commit()

    # Teste de Login Falhado
    response = test_client.post('/login', data={'email': 'user@test.com', 'password': 'wrongpassword'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Credenciais inv\xc3\xa1lidas" in response.data