# call_center_project/app/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, Empresa, Usuario, TicketSuporte, ReputacaoHistorico, AnotacaoTicket, TicketAtividade
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
import requests
from .ai_service import add_to_knowledge_base

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash("Você não tem permissão para acessar esta área.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_ticket_activity(ticket_id, activity_type, description):
    """Função auxiliar para registar atividades no ticket."""
    activity = TicketAtividade(
        ticket_id=ticket_id,
        user_id=current_user.id,
        activity_type=activity_type,
        description=description
    )
    db.session.add(activity)

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").count()
    empresas_ativas = Empresa.query.filter(Empresa.status_assinatura == 'ativa', Empresa.nome_empresa != "Sistema Call Center").count()
    empresas_bloqueadas = total_empresas - empresas_ativas
    return render_template('admin/dashboard.html', page_title="Dashboard do Administrador", total_empresas=total_empresas, empresas_ativas=empresas_ativas, empresas_bloqueadas=empresas_bloqueadas)

@bp.route('/')
@login_required
@admin_required
def index():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    return render_template('admin/index.html', empresas=empresas, page_title="Gerenciar Empresas")

@bp.route('/relatorio_empresas')
@login_required
@admin_required
def relatorio_empresas():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    return render_template('admin/relatorio_empresas.html', empresas=empresas, page_title="Relatório de Empresas", data_geracao=data_geracao)

@bp.route('/empresas/nova', methods=['GET', 'POST'])
@login_required
@admin_required
def nova_empresa():
    if request.method == 'POST':
        form_data = request.form
        data_vencimento_str = form_data.get('data_vencimento_pagamento')
        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d') if data_vencimento_str else None
        
        nova_empresa = Empresa(
            nome_empresa=form_data.get('nome_empresa'),
            cnpj=form_data.get('cnpj'),
            plano=form_data.get('plano'),
            telefone_contato=form_data.get('telefone_contato'),
            responsavel_contrato=form_data.get('responsavel_contrato'),
            forma_pagamento=form_data.get('forma_pagamento'),
            data_vencimento_pagamento=data_vencimento,
            monitorar_reputacao=True if form_data.get('monitorar_reputacao') == 'y' else False,
            google_reviews_url=form_data.get('google_reviews_url'),
            # --- CORREÇÃO APLICADA AQUI ---
            reclame_a_qui_url=form_data.get('reclame_aqui_url'),
            google_place_id=form_data.get('google_place_id')
        )
        
        db.session.add(nova_empresa)
        db.session.commit()
        
        novo_admin = Usuario(
            email=form_data.get('admin_email'),
            nome=form_data.get('admin_nome'),
            role='admin_empresa',
            empresa_id=nova_empresa.id
        )
        novo_admin.set_password(form_data.get('admin_senha'))
        db.session.add(novo_admin)
        db.session.commit()
        
        flash(f'Empresa "{nova_empresa.nome_empresa}" criada com sucesso!', 'success')
        return redirect(url_for('admin.index'))
        
    return render_template('admin/form_empresa.html', page_title="Nova Empresa", is_edit=False)

@bp.route('/empresas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        form = request.form
        
        empresa.nome_empresa = form.get('nome_empresa')
        empresa.cnpj = form.get('cnpj')
        empresa.plano = form.get('plano')
        empresa.telefone_contato = form.get('telefone_contato')
        empresa.responsavel_contrato = form.get('responsavel_contrato')
        empresa.forma_pagamento = form.get('forma_pagamento')
        data_vencimento_str = form.get('data_vencimento_pagamento')
        empresa.data_vencimento_pagamento = datetime.strptime(data_vencimento_str, '%Y-%m-%d') if data_vencimento_str else None
        empresa.monitorar_reputacao = True if form.get('monitorar_reputacao') == 'y' else False
        empresa.google_reviews_url = form.get('google_reviews_url')
        # --- CORREÇÃO APLICADA AQUI ---
        empresa.reclame_a_qui_url = form.get('reclame_aqui_url')
        empresa.google_place_id = form.get('google_place_id')

        novo_plano = empresa.plano
        
        if novo_plano == 'basico':
            empresa.plano_rh = False
            empresa.plano_ia = False
            empresa.plano_api = False
            empresa.plano_relatorios_avancados = False
            empresa.plano_suporte_prioritario = False
        elif novo_plano == 'medio':
            empresa.plano_rh = True
            empresa.plano_ia = False
            empresa.plano_api = False
            empresa.plano_relatorios_avancados = True
            empresa.plano_suporte_prioritario = False
        elif novo_plano == 'completo' or novo_plano == 'pro': # Incluindo 'pro' como completo
            empresa.plano_rh = True
            empresa.plano_ia = True
            empresa.plano_api = True
            empresa.plano_relatorios_avancados = True
            empresa.plano_suporte_prioritario = True
        
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

@bp.route('/historico')
@login_required
@admin_required
def historico_empresas():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    return render_template('admin/historico_empresas.html', empresas=empresas, page_title="Histórico e Infos de Empresas")

@bp.route('/historico/<int:id>')
@login_required
@admin_required
def detalhes_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    limite_plano = empresa.get_limite_usuarios()
    ultimo_registro = empresa.historico_reputacao[0] if empresa.historico_reputacao else None

    historico_reputacao_lista = list(empresa.historico_reputacao)
    
    labels = [h.data_registro.strftime('%d/%m/%Y') for h in reversed(historico_reputacao_lista)]
    notas_google = [h.nota_google for h in reversed(historico_reputacao_lista) if h.nota_google is not None]

    chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Nota Google', 'data': notas_google, 'borderColor': '#4285F4',
            'backgroundColor': 'rgba(66, 133, 244, 0.2)', 'fill': True, 'tension': 0.1
        }]
    }
    
    return render_template(
        'admin/detalhes_empresa.html', 
        empresa=empresa, 
        page_title=f"Dashboard de Reputação: {empresa.nome_empresa}", 
        ultimo_registro=ultimo_registro, 
        chart_data=chart_data, 
        limite_plano=limite_plano
    )

@bp.route('/historico/<int:id>/get_google_reviews')
@login_required
@admin_required
def get_google_reviews(id):
    empresa = Empresa.query.get_or_404(id)
    sample_reviews = { "reviews": [] } 
    return jsonify(sample_reviews)

@bp.route('/suporte')
@login_required
@admin_required
def listar_tickets():
    status_filtro = request.args.get('status', 'todos')
    prioridade_filtro = request.args.get('prioridade', 'todas')
    query = TicketSuporte.query
    if status_filtro != 'todos': query = query.filter_by(status=status_filtro)
    if prioridade_filtro != 'todas': query = query.filter_by(prioridade=prioridade_filtro)
    tickets = query.order_by(TicketSuporte.created_at.desc()).all()
    return render_template('admin/listar_tickets.html', tickets=tickets, page_title="Tickets de Suporte", status_filtro=status_filtro, prioridade_filtro=prioridade_filtro)

@bp.route('/suporte/ticket/<int:id>')
@login_required
@admin_required
def ver_ticket(id):
    ticket = TicketSuporte.query.get_or_404(id)
    super_admins = Usuario.query.filter_by(role='super_admin').order_by(Usuario.nome).all()
    return render_template('admin/ver_ticket.html', ticket=ticket, page_title=f"Ticket #{ticket.id}", super_admins=super_admins)

@bp.route('/suporte/ticket/<int:id>/mudar_status', methods=['POST'])
@login_required
@admin_required
def mudar_status_ticket(id):
    ticket = TicketSuporte.query.get_or_404(id)
    novo_status = request.form.get('novo_status')
    if novo_status in ['aberto', 'em_andamento', 'fechado'] and ticket.status != novo_status:
        log_ticket_activity(ticket.id, 'Mudança de Status', f'Status alterado de "{ticket.status}" para "{novo_status}".')
        ticket.status = novo_status
        db.session.commit()
        flash(f"O status do ticket #{ticket.id} foi atualizado.", "success")
    else:
        flash("Status inválido ou inalterado.", "warning")
    return redirect(url_for('admin.ver_ticket', id=id))

@bp.route('/suporte/ticket/<int:id>/adicionar_anotacao', methods=['POST'])
@login_required
@admin_required
def adicionar_anotacao(id):
    ticket = TicketSuporte.query.get_or_404(id)
    conteudo = request.form.get('conteudo')
    if not conteudo:
        flash('O conteúdo da anotação não pode estar vazio.', 'warning')
    else:
        nova_anotacao = AnotacaoTicket(ticket_id=ticket.id, autor_id=current_user.id, conteudo=conteudo)
        db.session.add(nova_anotacao)
        log_ticket_activity(ticket.id, 'Anotação', 'Anotação interna adicionada.')
        db.session.commit()
        flash('Anotação interna adicionada com sucesso.', 'success')
    return redirect(url_for('admin.ver_ticket', id=id))

@bp.route('/suporte/ticket/<int:id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_ticket(id):
    ticket = TicketSuporte.query.get_or_404(id)
    assignee_id = request.form.get('assignee_id')
    assignee = Usuario.query.get(assignee_id)
    
    if assignee and assignee.role == 'super_admin':
        ticket.assigned_to_id = assignee.id
        log_ticket_activity(ticket.id, 'Atribuição', f'Ticket atribuído a {assignee.nome}.')
        db.session.commit()
        flash(f'Ticket atribuído a {assignee.nome}.', 'success')
    else:
        flash('Operador inválido.', 'danger')
        
    return redirect(url_for('admin.ver_ticket', id=id))

@bp.route('/suporte/anotacao/<int:id>/mark_solution', methods=['POST'])
@login_required
@admin_required
def mark_solution(id):
    anotacao = AnotacaoTicket.query.get_or_404(id)
    ticket = anotacao.ticket
    AnotacaoTicket.query.filter_by(ticket_id=ticket.id, is_solution=True).update({'is_solution': False})
    
    anotacao.is_solution = True
    log_ticket_activity(ticket.id, 'Solução', f'Anotação #{anotacao.id} marcada como solução.')
    db.session.commit()
    flash('Anotação marcada como solução oficial do ticket.', 'success')
    return redirect(url_for('admin.ver_ticket', id=ticket.id))

@bp.route('/treinamento_ia')
@login_required
@admin_required
def treinamento_ia():
    tickets_resolvidos = db.session.query(TicketSuporte).join(AnotacaoTicket).filter(
        TicketSuporte.status == 'fechado',
        AnotacaoTicket.is_solution == True
    ).distinct().order_by(TicketSuporte.created_at.desc()).all()
    return render_template('admin/treinamento_ia.html', tickets=tickets_resolvidos, page_title="Treinamento da I.A.")

@bp.route('/treinamento_ia/add_to_kb', methods=['POST'])
@login_required
@admin_required
def add_to_kb():
    ticket_id = request.form.get('ticket_id')
    ticket = TicketSuporte.query.get_or_404(ticket_id)
    solucao = AnotacaoTicket.query.filter_by(ticket_id=ticket.id, is_solution=True).first()
    
    if not solucao:
        flash('Nenhuma solução marcada foi encontrada para este ticket.', 'danger')
    else:
        sucesso = add_to_knowledge_base(ticket.descricao, solucao.conteudo)
        if sucesso:
            flash('Novo conhecimento adicionado à I.A. com sucesso!', 'success')
        else:
            flash('Ocorreu um erro ao tentar treinar a I.A.', 'danger')
    
    return redirect(url_for('admin.treinamento_ia'))