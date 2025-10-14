# call_center_project/app/decorators.py

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify, g
from flask_login import current_user
from .models import Usuario

def require_plan(plan_level):
    """
    Decorador que restringe o acesso a rotas com base no plano da empresa.
    """
    # --- CORREÇÃO APLICADA AQUI ---
    # A estrutura correta de um decorador com argumentos precisa de uma função extra.
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.role == 'super_admin':
                return f(*args, **kwargs)

            empresa_plano = current_user.empresa.plano
            
            plan_hierarchy = {
                'basico': 1,
                'medio': 2,
                'completo': 3
            }

            if plan_hierarchy.get(empresa_plano, 0) < plan_hierarchy.get(plan_level, 99):
                flash(f'O seu plano "{empresa_plano.capitalize()}" não dá acesso a esta funcionalidade.', 'warning')
                return redirect(url_for('routes.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def agent_api_key_required(f):
    """Valida a chave de API enviada pelo agente de desktop."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({"error": "Header 'X-API-KEY' não fornecido."}), 401
            
        user = Usuario.query.filter_by(email=api_key).first()
        if not user or user.status != 'ativo':
            return jsonify({"error": "Chave de API inválida ou usuário inativo."}), 401
            
        g.current_user = user 
        return f(*args, **kwargs)
    return decorated_function

