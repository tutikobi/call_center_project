# app/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import db, Usuario
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Se já estiver logado, redireciona para o dashboard correto
        if current_user.role == 'super_admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('routes.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Credenciais inválidas. Por favor, tente novamente.')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        # --- LÓGICA DE REDIRECIONAMENTO CENTRALIZADA AQUI ---
        # Após o login, decide para onde enviar o utilizador
        if user.role == 'super_admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('routes.dashboard'))
        
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))