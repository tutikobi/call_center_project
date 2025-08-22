# call_center_project/app/decorators.py

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def require_plan(plan_level):
    """
    Decorador que restringe o acesso a rotas com base no plano da empresa.
    Ex: @require_plan('medio')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            # Super admin tem acesso a tudo
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