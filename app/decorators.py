# call_center_project/app/decorators.py

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify, g
from flask_login import current_user
from .models import Usuario

def require_plan(plan_level):
    """
    Decorador que restringe o acesso a rotas com base no plano da empresa.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.role == 'super_admin':
                return f(*args, **kwargs)

            empresa_plano = current_user.empresa.plano
            
            # --- CORREÇÃO APLICADA AQUI ---
            # Adicionado o plano 'pro' à hierarquia para que a verificação funcione corretamente.
            plan_hierarchy = {
                'basico': 1,
                'medio': 2,
                'pro': 3,
                'completo': 3,
                'customizado': 4
            }

            if plan_hierarchy.get(empresa_plano, 0) < plan_hierarchy.get(plan_level, 99):
                flash(f'O seu plano "{empresa_plano.capitalize()}" não dá acesso a esta funcionalidade.', 'warning')
                return redirect(url_for('routes.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- [INÍCIO DA NOVA ATUALIZAÇÃO] ---
def rh_access_required(f):
    """
    Decorador que restringe o acesso ao módulo RH.
    Permite acesso se o plano da empresa incluir RH E
    se o usuário for 'admin_empresa' OU tiver 'has_rh_access' = True.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # 1. Super admin sempre tem acesso
        if current_user.role == 'super_admin':
            return f(*args, **kwargs)

        # 2. Verifica se o plano da empresa contempla o RH
        # Usamos 'plano_rh' que é um booleano no modelo Empresa
        if not current_user.empresa.plano_rh:
            flash('O módulo RH não está habilitado no plano da sua empresa.', 'warning')
            return redirect(url_for('routes.dashboard'))

        # 3. Verifica se o usuário tem permissão individual (admin ou flag)
        if current_user.role == 'admin_empresa' or current_user.has_rh_access:
            return f(*args, **kwargs) # Acesso permitido!
        
        # 4. Se chegou até aqui, nega o acesso
        flash('Você não tem permissão para acessar o módulo RH.', 'danger')
        return redirect(url_for('routes.dashboard'))
    return decorated_function
# --- [FIM DA NOVA ATUALIZAÇÃO] ---

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