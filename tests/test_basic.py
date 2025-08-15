# tests/test_basic.py

def test_index_redirects_to_login_when_unauthenticated(test_client):
    """
    GIVEN um cliente Flask não autenticado
    WHEN a página inicial ('/') é requisitada
    THEN verifica se há um redirecionamento para a página de login
    """
    response = test_client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_page_loads_correctly(test_client):
    """
    GIVEN um cliente Flask
    WHEN a página de login ('/login') é requisitada
    THEN verifica se a página carrega com sucesso
    """
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data

def test_dashboard_requires_login(test_client):
    """
    GIVEN um cliente Flask não autenticado
    WHEN a página do dashboard ('/dashboard') é requisitada
    THEN verifica se há um redirecionamento para a página de login
    """
    response = test_client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location