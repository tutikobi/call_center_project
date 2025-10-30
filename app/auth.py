# app/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import db, Usuario
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'super_admin':
            # O super_admin logado deve ser redirecionado para o dashboard de admin
            return redirect(url_for('admin.dashboard')) 
        # Outros utilizadores logados vão para o dashboard de RH
        return redirect(url_for('rh.dashboard')) # <-- ALTERADO DE 'routes.dashboard'
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Credenciais inválidas. Por favor, tente novamente.')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=True)
        
        if user.role == 'super_admin':
            # Após o login, o super_admin vai para o dashboard de admin
            return redirect(url_for('admin.dashboard'))
        else:
            # Outros utilizadores vão para o dashboard de RH
            return redirect(url_for('rh.dashboard')) # <-- ALTERADO DE 'routes.dashboard'
        
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('auth.login'))
