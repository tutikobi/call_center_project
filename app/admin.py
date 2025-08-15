# call_center_project/app/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, Empresa, Usuario, TicketSuporte
from flask_login import login_required, current_user
from functools import wraps
import re
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash("Você não tem permissão para acessar esta área.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ROTA PARA O DASHBOARD DO ADMIN (COM MÉTRICAS E GRÁFICOS)
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").count()
    empresas_ativas = Empresa.query.filter(Empresa.status_assinatura == 'ativa', Empresa.nome_empresa != "Sistema Call Center").count()
    empresas_bloqueadas = total_empresas - empresas_ativas
    
    return render_template('admin/dashboard.html', 
                           page_title="Dashboard do Administrador",
                           total_empresas=total_empresas,
                           empresas_ativas=empresas_ativas,
                           empresas_bloqueadas=empresas_bloqueadas)

# ROTA PARA GERENCIAR EMPRESAS (APENAS A TABELA)
@bp.route('/')
@login_required
@admin_required
def index():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    return render_template('admin/index.html', 
                           empresas=empresas, 
                           page_title="Gerenciar Empresas")

# ROTA PARA O RELATÓRIO DE EMPRESAS
@bp.route('/relatorio_empresas')
@login_required
@admin_required
def relatorio_empresas():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    return render_template('admin/relatorio_empresas.html', 
                           empresas=empresas, 
                           page_title="Relatório de Empresas",
                           data_geracao=data_geracao)

# --- Funções de validação e CRUD de empresas (permanecem as mesmas) ---

def is_valid_cnpj(cnpj):
    if not cnpj: return False
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj) == 14

def is_valid_email(email):
    if not email: return False
    return re.match(r'[^@\s]+@[^@\s]+\.[^@\s]+', email)

@bp.route('/empresas/nova', methods=['GET', 'POST'])
@login_required
@admin_required
def nova_empresa():
    if request.method == 'POST':
        nome_empresa = request.form.get('nome_empresa')
        cnpj = request.form.get('cnpj')
        telefone_contato = request.form.get('telefone_contato')
        admin_nome = request.form.get('admin_nome')
        admin_email = request.form.get('admin_email')
        admin_senha = request.form.get('admin_senha')
        form_data = request.form
        if not all([nome_empresa, cnpj, admin_nome, admin_email, admin_senha]):
            flash('Todos os campos, exceto telefone, são obrigatórios.', 'warning')
            return render_template('admin/form_empresa.html', page_title="Nova Empresa", form_data=form_data)
        if not is_valid_cnpj(cnpj):
            flash('O CNPJ informado é inválido.', 'danger')
            return render_template('admin/form_empresa.html', page_title="Nova Empresa", form_data=form_data)
        if not is_valid_email(admin_email):
            flash('O Email do administrador informado é inválido.', 'danger')
            return render_template('admin/form_empresa.html', page_title="Nova Empresa", form_data=form_data)
        if Empresa.query.filter_by(cnpj=cnpj).first():
            flash(f'O CNPJ "{cnpj}" já está cadastrado.', 'danger')
            return render_template('admin/form_empresa.html', page_title="Nova Empresa", form_data=form_data)
        if Usuario.query.filter_by(email=admin_email).first():
            flash(f'O email "{admin_email}" já está em uso.', 'danger')
            return render_template('admin/form_empresa.html', page_title="Nova Empresa", form_data=form_data)
        nova_empresa = Empresa(nome_empresa=nome_empresa, cnpj=cnpj, telefone_contato=telefone_contato)
        db.session.add(nova_empresa)
        db.session.commit()
        novo_admin = Usuario(email=admin_email, nome=admin_nome, role='admin_empresa', empresa_id=nova_empresa.id)
        novo_admin.set_password(admin_senha)
        db.session.add(novo_admin)
        db.session.commit()
        flash(f'Empresa "{nome_empresa}" criada com sucesso!', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/form_empresa.html', page_title="Nova Empresa")

@bp.route('/empresas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        empresa.nome_empresa = request.form.get('nome_empresa')
        empresa.cnpj = request.form.get('cnpj')
        empresa.telefone_contato = request.form.get('telefone_contato')
        if not is_valid_cnpj(empresa.cnpj):
            flash('O CNPJ informado é inválido.', 'danger')
            return render_template('admin/form_empresa.html', page_title=f"Editar Empresa: {empresa.nome_empresa}", empresa=empresa, is_edit=True)
        empresa_existente = Empresa.query.filter(Empresa.id != id, Empresa.cnpj == empresa.cnpj).first()
        if empresa_existente:
            flash(f'O CNPJ "{empresa.cnpj}" já pertence a outra empresa.', 'danger')
            return render_template('admin/form_empresa.html', page_title=f"Editar Empresa: {empresa.nome_empresa}", empresa=empresa, is_edit=True)
        db.session.commit()
        flash(f'Dados da empresa "{empresa.nome_empresa}" atualizados com sucesso!', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/form_empresa.html', page_title=f"Editar Empresa: {empresa.nome_empresa}", empresa=empresa, is_edit=True)

@bp.route('/empresas/<int:id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_status(id):
    empresa = Empresa.query.get_or_404(id)
    if empresa.nome_empresa == "Sistema Call Center":
        flash("A empresa do sistema não pode ser modificada.", "danger")
        return redirect(url_for('admin.index'))
    if empresa.status_assinatura == 'ativa':
        empresa.status_assinatura = 'bloqueada'
        flash(f'O acesso da empresa "{empresa.nome_empresa}" foi bloqueado.', 'warning')
    else:
        empresa.status_assinatura = 'ativa'
        flash(f'O acesso da empresa "{empresa.nome_empresa}" foi reativado.', 'success')
    db.session.commit()
    return redirect(url_for('admin.index'))

@bp.route('/empresas/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if empresa.nome_empresa == "Sistema Call Center":
        flash("A empresa do sistema não pode ser excluída.", "danger")
        return redirect(url_for('admin.index'))
    db.session.delete(empresa)
    db.session.commit()
    flash(f'A empresa "{empresa.nome_empresa}" e todos os seus dados foram excluídos permanentemente.', 'danger')
    return redirect(url_for('admin.index'))

@bp.route('/suporte')
@login_required
@admin_required
def listar_tickets():
    status_filtro = request.args.get('status', 'todos')
    prioridade_filtro = request.args.get('prioridade', 'todas')
    query = TicketSuporte.query
    if status_filtro != 'todos':
        query = query.filter_by(status=status_filtro)
    if prioridade_filtro != 'todas':
        query = query.filter_by(prioridade=prioridade_filtro)
    tickets = query.order_by(TicketSuporte.data_criacao.desc()).all()
    return render_template('admin/listar_tickets.html', tickets=tickets, page_title="Tickets de Suporte", status_filtro=status_filtro, prioridade_filtro=prioridade_filtro)

@bp.route('/suporte/ticket/<int:id>')
@login_required
@admin_required
def ver_ticket(id):
    ticket = TicketSuporte.query.get_or_404(id)
    return render_template('admin/ver_ticket.html', ticket=ticket, page_title=f"Ticket #{ticket.id}")

@bp.route('/suporte/ticket/<int:id>/mudar_status', methods=['POST'])
@login_required
@admin_required
def mudar_status_ticket(id):
    ticket = TicketSuporte.query.get_or_404(id)
    novo_status = request.form.get('novo_status')
    if novo_status in ['aberto', 'em_andamento', 'fechado']:
        ticket.status = novo_status
        db.session.commit()
        flash(f"O status do ticket #{ticket.id} foi atualizado para '{novo_status}'.", "success")
    else:
        flash("Status inválido.", "danger")
    return redirect(url_for('admin.ver_ticket', id=id))