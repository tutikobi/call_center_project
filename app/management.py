# call_center_project/app/management.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, Usuario, Empresa, TicketSuporte
from flask_login import login_required, current_user
from functools import wraps

bp = Blueprint('management', __name__, url_prefix='/management' )

# --- LIMITES DE PLANOS ATUALIZADOS ---
PLAN_LIMITS = {
    'basico': 5,
    'medio': 10,
    'pro': 20
}

def empresa_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin_empresa':
            flash("Você não tem permissão para acessar esta área.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/usuarios')
@login_required
@empresa_admin_required
def listar_usuarios():
    usuarios_da_empresa = Usuario.query.filter_by(empresa_id=current_user.empresa_id).order_by(Usuario.nome).all()
    return render_template('management/listar_usuarios.html', usuarios=usuarios_da_empresa, page_title="Gerenciar Usuários")

@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def novo_usuario():
    # --- LÓGICA DE VERIFICAÇÃO DE LIMITE ATIVADA ---
    empresa_atual = current_user.empresa
    plano_da_empresa = empresa_atual.plano
    limite_agentes = PLAN_LIMITS.get(plano_da_empresa, 0)

    # Conta apenas os "agentes" e "admin_empresa" para o limite
    total_usuarios = Usuario.query.filter(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.role.in_(['agente', 'admin_empresa'])
    ).count()

    if total_usuarios >= limite_agentes:
        flash(f'O limite de {limite_agentes} usuários para o plano "{plano_da_empresa.capitalize()}" foi atingido.', 'danger')
        return redirect(url_for('management.listar_usuarios'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        role = request.form.get('role', 'agente')
        if not all([nome, email, senha]):
            flash('Todos os campos são obrigatórios.', 'warning')
            return render_template('management/form_usuario.html', page_title="Novo Usuário")
        if Usuario.query.filter_by(email=email).first():
            flash(f'O email "{email}" já está em uso.', 'danger')
            return render_template('management/form_usuario.html', page_title="Novo Usuário", form_data=request.form)
        
        novo_usuario = Usuario(nome=nome, email=email, role=role, empresa_id=current_user.empresa_id)
        novo_usuario.set_password(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        flash(f'Usuário "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('management.listar_usuarios'))
        
    return render_template('management/form_usuario.html', page_title="Novo Usuário")

@bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.role = request.form.get('role')
        email_existente = Usuario.query.filter(Usuario.id != id, Usuario.email == usuario.email).first()
        if email_existente:
            flash(f'O email "{usuario.email}" já pertence a outro usuário.', 'danger')
            return render_template('management/form_usuario.html', page_title=f"Editar Usuário: {usuario.nome}", usuario=usuario, is_edit=True)
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.set_password(nova_senha)
            flash('Senha atualizada com sucesso.', 'info')
        db.session.commit()
        flash(f'Dados do usuário "{usuario.nome}" atualizados com sucesso!', 'success')
        return redirect(url_for('management.listar_usuarios'))
    return render_template('management/form_usuario.html', page_title=f"Editar Usuário: {usuario.nome}", usuario=usuario, is_edit=True)

@bp.route('/usuarios/<int:id>/toggle_status', methods=['POST'])
@login_required
@empresa_admin_required
def toggle_status_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.id == current_user.id:
        flash("Você não pode bloquear seu próprio acesso.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.status == 'ativo':
        usuario.status = 'bloqueado'
        flash(f'O acesso do usuário "{usuario.nome}" foi bloqueado.', 'warning')
    else:
        usuario.status = 'ativo'
        flash(f'O acesso do usuário "{usuario.nome}" foi reativado.', 'success')
    db.session.commit()
    return redirect(url_for('management.listar_usuarios'))

@bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_required
@empresa_admin_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.id == current_user.id:
        flash("Você não pode excluir seu próprio usuário.", 'danger')
        return redirect(url_for('management.listar_usuarios'))
    db.session.delete(usuario)
    db.session.commit()
    flash(f'O usuário "{usuario.nome}" foi excluído permanentemente.', 'danger')
    return redirect(url_for('management.listar_usuarios'))

@bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def configuracoes():
    empresa = Empresa.query.get(current_user.empresa_id)
    if request.method == 'POST':
        empresa.whatsapp_token = request.form.get('whatsapp_token')
        empresa.whatsapp_url = request.form.get('whatsapp_url')
        empresa.webhook_verify_token = request.form.get('webhook_verify_token')
        db.session.commit()
        flash('Configurações de API salvas com sucesso!', 'success')
        return redirect(url_for('management.configuracoes'))
    return render_template('management/configuracoes.html', empresa=empresa, page_title="Configurações da API")

@bp.route('/suporte/novo_ticket', methods=['POST'])
@login_required
def novo_ticket():
    if current_user.role == 'super_admin':
        flash("O super admin não pode abrir tickets.", "danger")
        return redirect(request.referrer or url_for('routes.dashboard'))

    assunto = request.form.get('assunto')
    descricao = request.form.get('descricao')

    if not all([assunto, descricao]):
        flash("Todos os campos do ticket são obrigatórios.", "warning")
        return redirect(request.referrer or url_for('routes.dashboard'))

    if assunto in ["Suporte Técnico", "Problema em Relatórios"]:
        prioridade = "alta"
    elif assunto == "Emissão de Fatura":
        prioridade = "media"
    else:
        prioridade = "baixa"

    novo_ticket = TicketSuporte(
        assunto=assunto,
        descricao=descricao,
        prioridade=prioridade,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id
    )
    db.session.add(novo_ticket)
    db.session.commit()

    flash("Seu ticket de suporte foi enviado com sucesso! Entraremos em contato em breve.", "success")
    return redirect(request.referrer or url_for('routes.dashboard'))