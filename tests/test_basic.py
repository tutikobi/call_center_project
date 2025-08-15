# tests/test_basic.py

def test_index_redirect(test_client):
    """
    GIVEN um cliente Flask configurado para teste
    WHEN a página inicial ('/') é requisitada (GET)
    THEN verifica se há um redirecionamento (status 302)
    """
    response = test_client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location or '/dashboard' in response.location

def test_login_page_loads(test_client):
    """
    GIVEN um cliente Flask configurado para teste
    WHEN a página de login ('/login') é requisitada (GET)
    THEN verifica se a página carrega com sucesso (status 200)
    """
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data  # Verifica se a palavra "Login" está no HTML

def test_dashboard_requires_login(test_client):
    """
    GIVEN um cliente Flask configurado para teste
    WHEN a página do dashboard ('/dashboard') é requisitada sem login
    THEN verifica se há um redirecionamento para a página de login
    """
    response = test_client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location