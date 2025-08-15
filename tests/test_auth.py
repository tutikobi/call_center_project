# tests/test_auth.py

from app.models import Usuario, Empresa
from app import db

def test_login_logout(test_client):
    """
    GIVEN um cliente Flask e uma base de dados de teste
    WHEN um utilizador de teste é criado e tenta fazer login
    THEN verifica se o login é bem-sucedido, o acesso ao dashboard é permitido e o logout funciona
    """
    # Configuração: Criar uma empresa e um utilizador de teste
    empresa = Empresa(nome_empresa="Empresa Teste", cnpj="00.000.000/0000-11")
    db.session.add(empresa)
    db.session.commit()
    
    user = Usuario(email="test@example.com", nome="Test User", empresa_id=empresa.id, role="agente")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Teste 1: Login com credenciais corretas
    response = test_client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Login" not in response.data

    # Teste 2: Logout
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_with_wrong_credentials(test_client):
    """
    GIVEN um cliente Flask
    WHEN uma tentativa de login é feita com uma palavra-passe errada
    THEN verifica se uma mensagem de erro é exibida
    """
    # --- BLOCO DE CONFIGURAÇÃO ADICIONADO AQUI ---
    # Agora este teste cria o seu próprio utilizador e não depende de mais nenhum.
    empresa = Empresa(nome_empresa="Empresa Teste Wrong Pass", cnpj="00.000.000/0000-22")
    db.session.add(empresa)
    db.session.commit()
    
    user = Usuario(email="test2@example.com", nome="Test User 2", empresa_id=empresa.id, role="agente")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    # --- FIM DO BLOCO DE CONFIGURAÇÃO ---

    response = test_client.post('/login', data={
        'email': 'test2@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Credenciais inv\xc3\xa1lidas" in response.data