# tests/test_auth.py

from app.models import Usuario, Empresa
from app import db

def test_successful_agent_login_and_logout(test_client):
    """
    GIVEN um utilizador 'agente' existe na base de dados
    WHEN ele faz login com as credenciais corretas
    THEN verifica se é redirecionado para o dashboard de agente e se o logout funciona
    """
    # Configuração
    empresa = Empresa(nome_empresa="Empresa Teste", cnpj="11.111.111/0001-11")
    db.session.add(empresa)
    db.session.commit()
    user = Usuario(email="agent@test.com", nome="Test Agent", empresa_id=empresa.id, role="agente")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Teste de Login
    response = test_client.post('/login', data={
        'email': 'agent@test.com',
        'password': 'password12ajudante123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Dashboard Unificado" in response.data # Conteúdo específico do dashboard de agente
    assert b"Dashboard do Administrador" not in response.data

    # Teste de Logout
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Dashboard Unificado" not in response.data

def test_successful_superadmin_login(test_client):
    """
    GIVEN um utilizador 'super_admin' existe na base de dados
    WHEN ele faz login com as credenciais corretas
    THEN verifica se é redirecionado para o dashboard de superadmin
    """
    # Configuração
    empresa = Empresa(nome_empresa="Sistema", cnpj="22.222.222/0001-22")
    db.session.add(empresa)
    db.session.commit()
    user = Usuario(email="superadmin@test.com", nome="Test Super Admin", empresa_id=empresa.id, role="super_admin")
    user.set_password("superpassword")
    db.session.add(user)
    db.session.commit()

    # Teste de Login
    response = test_client.post('/login', data={
        'email': 'superadmin@test.com',
        'password': 'superpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Dashboard do Administrador" in response.data # Conteúdo específico do dashboard de admin
    assert b"Dashboard Unificado" not in response.data

def test_login_with_wrong_password(test_client):
    """
    GIVEN um utilizador existe na base de dados
    WHEN ele tenta fazer login com a palavra-passe errada
    THEN verifica se uma mensagem de erro é exibida
    """
    # Configuração
    empresa = Empresa(nome_empresa="Empresa Teste", cnpj="33.333.333/0001-33")
    db.session.add(empresa)
    db.session.commit()
    user = Usuario(email="user@test.com", nome="Test User", empresa_id=empresa.id, role="agente")
    user.set_password("correctpassword")
    db.session.add(user)
    db.session.commit()

    # Teste de Login Falhado
    response = test_client.post('/login', data={
        'email': 'user@test.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Credenciais inv\xc3\xa1lidas" in response.data # Verifica a mensagem de erro