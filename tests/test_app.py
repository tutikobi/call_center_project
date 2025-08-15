# tests/test_app.py

def test_index_redirects_to_login_when_unauthenticated(test_client):
    """Verifica se a página inicial ('/') redireciona para a página de login."""
    response = test_client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_page_loads(test_client):
    """Verifica se a página de login ('/login') carrega com sucesso."""
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data

def test_protected_page_requires_login(test_client):
    """Verifica se uma página protegida como '/dashboard' redireciona para o login."""
    response = test_client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location