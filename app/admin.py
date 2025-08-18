# call_center_project/app/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, Empresa, Usuario, TicketSuporte, ReputacaoHistorico, AnotacaoTicket
from flask_login import login_required, current_user
from functools import wraps
import re
from datetime import datetime
import requests
from .management import PLAN_LIMITS # --- IMPORTAÇÃO CORRIGIDA AQUI ---

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash("Você não tem permissão para acessar esta área.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE REPUTAÇÃO ---
@bp.route('/historico/<int:id>/get_google_reviews')
@login_required
@admin_required
def get_google_reviews(id):
    empresa = Empresa.query.get_or_404(id)
    sample_reviews = {
        "reviews": [
            { "reviewer": {"displayName": "Gabriela Bareta"}, "starRating": "FIVE", "comment": "Não tenho dúvidas que, colocar meu imóvel para alugar na Barcellos, foi a melhor escolha...", "reply": { "comment": "Queremos expressar nossa mais profunda gratidão..."}},
            { "reviewer": {"displayName": "Carlos Silva"}, "starRating": "ONE", "comment": "Péssima experiência. O atendimento demorou e não resolveram o meu problema.", "reply": None}
        ], "totalReviewCount": 215
    }
    return jsonify(sample_reviews)

@bp.route('/historico/<int:id>/buscar_dados_reputacao')
@login_required
@admin_required
def buscar_dados_reputacao(id):
    from flask import current_app
    empresa = Empresa.query.get_or_404(id)
    api_key = current_app.config.get('GOOGLE_PLACES_API_KEY')
    place_id = empresa.google_place_id
    if not api_key or api_key == 'SUA_CHAVE_API_AQUI': return jsonify({'error': 'A chave da API do Google não foi configurada no sistema.'}), 500
    if not place_id: return jsonify({'error': 'O "Google Place ID" desta empresa não foi configurado.'}), 400
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=rating,user_ratings_total&key={api_key}&language=pt_BR"
    dados_encontrados = {'nota_google': None, 'total_avaliacoes_google': None}
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'OK' and 'result' in data:
            result = data['result']
            dados_encontrados['nota_google'] = result.get('rating')
            dados_encontrados['total_avaliacoes_google'] = result.get('user_ratings_total')
        else:
            return jsonify({'error': data.get('error_message', 'Erro ao comunicar com a API do Google.')}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Falha na comunicação com o Google: {e}'}), 500
    return jsonify(dados_encontrados)

@bp.route('/historico/<int:id>')
@login_required
@admin_required
def detalhes_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    ultimo_registro = empresa.historico_reputacao[0] if empresa.historico_reputacao else None
    limite_plano = PLAN_LIMITS.get(empresa.plano, 0)
    historico_reverso = reversed(empresa.historico_reputacao)
    labels = [h.data_registro.strftime('%d/%m/%Y') for h in historico_reverso]
    historico_reverso = reversed(empresa.historico_reputacao)
    notas_google = [h.nota_google for h in historico_reverso if h.nota_google is not None]
    chart_data = {'labels': labels, 'datasets': [{'label': 'Nota Google', 'data': notas_google, 'borderColor': '#4285F4', 'backgroundColor': 'rgba(66, 133, 244, 0.2)', 'fill': True, 'tension': 0.1}]}
    return render_template('admin/detalhes_empresa.html', empresa=empresa, page_title=f"Dashboard de Reputação: {empresa.nome_empresa}", ultimo_registro=ultimo_registro, chart_data=chart_data, limite_plano=limite_plano)

@bp.route('/historico/<int:id>/adicionar_registro', methods=['POST'])
@login_required
@admin_required
def adicionar_registro_reputacao(id):
    empresa = Empresa.query.get_or_404(id)
    try:
        nota_google_str = request.form.get('nota_google')
        total_avaliacoes_google_str = request.form.get('total_avaliacoes_google')
        novo_registro = ReputacaoHistorico(empresa_id=empresa.id, nota_google=float(nota_google_str) if nota_google_str else None, total_avaliacoes_google=int(total_avaliacoes_google_str) if total_avaliacoes_google_str else None, observacoes="Registo via Verificador de Reputação.")
        db.session.add(novo_registro)
        db.session.commit()
        flash('Novo registo de reputação confirmado e guardado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar registo: {e}', 'danger')
    return redirect(url_for('admin.detalhes_empresa', id=id))

@bp.route('/historico')
@login_required
@admin_required
def historico_empresas():
    empresas = Empresa.query.filter(Empresa.nome_empresa != "Sistema Call Center").order_by(Empresa.nome_empresa).all()
    return render_template('admin/historico_empresas.html', empresas=empresas, page_title="Histórico e Infos de Empresas")

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
        nova_empresa = Empresa(nome_empresa=form_data.get('nome_empresa'), cnpj=form_data.get('cnpj'), plano=form_data.get('plano'), telefone_contato=form_data.get('telefone_contato'), responsavel_contrato=form_data.get('responsavel_contrato'), forma_pagamento=form_data.get('forma_pagamento'), data_vencimento_pagamento=data_vencimento, monitorar_reputacao=True if form_data.get('monitorar_reputacao') == 'y' else False, google_reviews_url=form_data.get('google_reviews_url'), reclame_aqui_url=form_data.get('reclame_aqui_url'), google_place_id=form_data.get('google_place_id'))
        db.session.add(nova_empresa)
        db.session.commit()
        novo_admin = Usuario(email=form_data.get('admin_email'), nome=form_data.get('admin_nome'), role='admin_empresa', empresa_id=nova_empresa.id)
        novo_admin.set_password(form_data.get('admin_senha'))
        db.session.add(novo_admin)
        db.session.commit()
        flash(f'Empresa "{nova_empresa.nome_empresa}" criada com sucesso!', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/form_empresa.html', page_title="Nova Empresa")

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
        empresa.reclame_aqui_url = form.get('reclame_aqui_url')
        empresa.google_place_id = form.get('google_place_id')
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
    if status_filtro != 'todos': query = query.filter_by(status=status_filtro)
    if prioridade_filtro != 'todas': query = query.filter_by(prioridade=prioridade_filtro)
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

@bp.route('/suporte/ticket/<int:id>/adicionar_anotacao', methods=['POST'])
@login_required
@admin_required
def adicionar_anotacao(id):
    ticket = TicketSuporte.query.get_or_404(id)
    conteudo_anotacao = request.form.get('conteudo')
    if not conteudo_anotacao:
        flash('O conteúdo da anotação não pode estar vazio.', 'warning')
        return redirect(url_for('admin.ver_ticket', id=id))
    nova_anotacao = AnotacaoTicket(ticket_id=ticket.id, autor_id=current_user.id, conteudo=conteudo_anotacao)
    db.session.add(nova_anotacao)
    db.session.commit()
    flash('Anotação interna adicionada com sucesso.', 'success')
    return redirect(url_for('admin.ver_ticket', id=id))