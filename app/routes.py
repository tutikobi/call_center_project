# call_center_project/app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from .models import db, Avaliacao, ConversaWhatsApp, Usuario, Notificacao, Email, ActivityLog
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, date, timedelta
from .decorators import require_plan

bp = Blueprint('routes', __name__)

# ... (código existente das rotas, sem alterações, até o final do arquivo) ...
@bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == 'super_admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for('auth.login'))

@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'super_admin':
        return redirect(url_for('admin.dashboard'))
        
    empresa_id_do_usuario = current_user.empresa_id
    total_avaliacoes = db.session.query(Avaliacao.id).filter_by(empresa_id=empresa_id_do_usuario).count()
    conversas_ativas = db.session.query(ConversaWhatsApp.id).filter_by(empresa_id=empresa_id_do_usuario, status='ativo').count()
    csat_geral_query = db.session.query(func.avg(Avaliacao.csat)).filter_by(empresa_id=empresa_id_do_usuario).scalar()
    csat_geral = round(csat_geral_query, 1) if csat_geral_query else 'N/A'
    
    agentes_online = Usuario.query.filter(Usuario.empresa_id == empresa_id_do_usuario, Usuario.role.in_(['agente', 'admin_empresa'])).order_by(Usuario.nome).all()
    
    return render_template("dashboard.html", 
                         total_avaliacoes=total_avaliacoes,
                         conversas_ativas=conversas_ativas,
                         csat_geral=csat_geral,
                         agentes_online=agentes_online)

@bp.route("/dashboard/agente/<int:agente_id>")
@login_required
def dashboard_agente(agente_id):
    if current_user.role == 'agente' and current_user.id != agente_id:
        flash("Acesso não permitido.", "danger")
        return redirect(url_for('routes.dashboard'))
    
    agente = Usuario.query.get_or_404(agente_id)

    if current_user.role == 'admin_empresa' and agente.empresa_id != current_user.empresa_id:
        flash("Agente não encontrado na sua empresa.", "danger")
        return redirect(url_for('routes.dashboard'))

    total_avaliacoes = Avaliacao.query.filter_by(agente_id=agente.id).count()
    csat_medio_query = db.session.query(func.avg(Avaliacao.csat)).filter_by(agente_id=agente.id).scalar()
    csat_medio = round(csat_medio_query, 1) if csat_medio_query else 'N/A'
    conversas_atribuidas = ConversaWhatsApp.query.filter_by(agente_atribuido_id=agente.id).count()

    atendimentos_por_canal = db.session.query(
        Avaliacao.canal, func.count(Avaliacao.id)
    ).filter_by(agente_id=agente.id).group_by(Avaliacao.canal).all()
    
    chart_data = {
        'labels': [item[0].capitalize() for item in atendimentos_por_canal],
        'data': [item[1] for item in atendimentos_por_canal]
    }

    ultimas_avaliacoes = Avaliacao.query.filter_by(agente_id=agente.id).order_by(Avaliacao.created_at.desc()).limit(5).all()

    return render_template("dashboard_agente.html",
                           agente=agente,
                           total_avaliacoes=total_avaliacoes,
                           csat_medio=csat_medio,
                           conversas_atribuidas=conversas_atribuidas,
                           chart_data=chart_data,
                           ultimas_avaliacoes=ultimas_avaliacoes)

@bp.route("/avaliar", methods=["GET", "POST"])
@login_required
def avaliar():
    agentes_da_empresa = Usuario.query.filter_by(empresa_id=current_user.empresa_id).order_by(Usuario.nome).all()

    if request.method == "POST":
        agente_selecionado_id = request.form.get("agente_id")
        
        if not agente_selecionado_id:
            flash("Por favor, selecione um agente.", "warning")
            return render_template("avaliar.html", agentes=agentes_da_empresa)

        avaliacao = Avaliacao(
            agente_id=agente_selecionado_id,
            empresa_id=current_user.empresa_id,
            canal=request.form.get("canal"),
            chamada_id=request.form.get("chamada_id"),
            csat=float(request.form.get("csat", 0)),
            observacoes=request.form.get("observacoes")
        )
        db.session.add(avaliacao)
        db.session.commit()
        flash("Avaliação registrada com sucesso!", "success")
        return redirect(url_for("routes.dashboard"))
    
    return render_template("avaliar.html", agentes=agentes_da_empresa)

@bp.route("/relatorios", methods=['GET', 'POST'])
@login_required
def relatorios():
    agentes = Usuario.query.filter_by(empresa_id=current_user.empresa_id).order_by(Usuario.nome).all()
    dados_relatorio = None
    filtros_aplicados = {}
    if request.method == 'POST':
        periodo = request.form.get('periodo')
        canal = request.form.get('canal')
        agente_id = request.form.get('agente')
        filtros_aplicados = {'periodo': periodo, 'canal': canal, 'agente_id': agente_id}
        query = Avaliacao.query.filter_by(empresa_id=current_user.empresa_id)
        if periodo and periodo != 'todos':
            try:
                dias = int(periodo.replace('d', ''))
                data_inicio = datetime.utcnow() - timedelta(days=dias)
                query = query.filter(Avaliacao.created_at >= data_inicio)
            except ValueError:
                pass 
        if canal and canal != 'todos':
            query = query.filter_by(canal=canal)
        if agente_id and agente_id != 'todos':
            query = query.filter_by(agente_id=int(agente_id))
        
        dados_relatorio = query.order_by(Avaliacao.created_at.desc()).all()

    return render_template("relatorios.html", 
        agentes=agentes, 
        dados_relatorio=dados_relatorio,
        filtros=filtros_aplicados
    )

@bp.route("/conversas")
@login_required
def conversas():
    query_conversas = ConversaWhatsApp.query.filter_by(
        empresa_id=current_user.empresa_id,
        status='ativo'
    )

    if current_user.role == 'agente':
        query_conversas = query_conversas.filter(ConversaWhatsApp.agente_atribuido_id == current_user.id)

    conversas_ativas = query_conversas.order_by(ConversaWhatsApp.inicio.desc()).all()

    agentes_da_empresa = Usuario.query.filter(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.role.in_(['agente', 'admin_empresa'])
    ).order_by(Usuario.nome).all()

    return render_template("conversas.html", 
                           conversas=conversas_ativas,
                           agentes=agentes_da_empresa)

@bp.route('/conversa/<int:conversa_id>/atribuir', methods=['POST'])
@login_required
def atribuir_conversa(conversa_id):
    if current_user.role != 'admin_empresa':
        flash('Apenas administradores podem atribuir conversas.', 'danger')
        return redirect(url_for('routes.conversas'))

    conversa = ConversaWhatsApp.query.get_or_404(conversa_id)
    agente_id = request.form.get('agente_id')

    if not agente_id or agente_id == 'nenhum':
        conversa.agente_atribuido_id = None
        agente_nome = "ninguém"
    else:
        agente = Usuario.query.get(agente_id)
        if agente and agente.empresa_id == current_user.empresa_id:
            conversa.agente_atribuido_id = agente.id
            agente_nome = agente.nome
        else:
            flash('Agente inválido.', 'danger')
            return redirect(url_for('routes.conversas'))

    db.session.commit()
    flash(f'Conversa com {conversa.nome_cliente} foi atribuída a {agente_nome}.', 'success')
    return redirect(url_for('routes.conversas'))

@bp.route("/emails")
@login_required
def emails():
    if current_user.empresa.plano not in ['medio', 'pro', 'premium', 'completo', 'customizado']:
        flash("O seu plano não tem acesso à funcionalidade de Email.", "warning")
        return redirect(url_for('routes.dashboard'))

    if current_user.role == 'admin_empresa':
        agentes = Usuario.query.filter(
            Usuario.empresa_id == current_user.empresa_id,
            Usuario.role == 'agente'
        ).order_by(Usuario.nome).all()
        return render_template("emails.html", page_title="Monitoramento de Email", agentes=agentes)
    
    return redirect(url_for('routes.caixa_email_agente', agente_id=current_user.id))

@bp.route("/emails/agente/<int:agente_id>")
@login_required
def caixa_email_agente(agente_id):
    if current_user.role == 'admin_empresa':
        agente = Usuario.query.filter_by(id=agente_id, empresa_id=current_user.empresa_id).first_or_404()
    elif current_user.role == 'agente':
        if current_user.id != agente_id:
            flash("Acesso não permitido.", "danger")
            return redirect(url_for('routes.dashboard'))
        agente = current_user
    else:
        return redirect(url_for('routes.dashboard'))

    today_start = datetime.combine(date.today(), datetime.min.time())
    
    emails_recebidos_hoje = Email.query.filter(
        Email.agente_id == agente.id,
        Email.data_recebimento >= today_start
    ).count()

    emails_respondidos = Email.query.filter_by(agente_id=agente.id, status='respondido').count()
    emails_nao_lidos = Email.query.filter_by(agente_id=agente.id, status='nao_lido').count()
    
    lista_de_emails = Email.query.filter_by(agente_id=agente.id).order_by(Email.data_recebimento.desc()).all()

    return render_template("caixa_email_agente.html", 
                           page_title=f"Caixa de Entrada de {agente.nome}",
                           agente=agente,
                           emails_recebidos_hoje=emails_recebidos_hoje,
                           emails_respondidos=emails_respondidos,
                           emails_nao_lidos=emails_nao_lidos,
                           lista_de_emails=lista_de_emails)

@bp.route("/email/<int:email_id>")
@login_required
def ver_email(email_id):
    query = Email.query.filter_by(id=email_id)
    email = query.filter(Email.empresa_id == current_user.empresa_id).first_or_404()
    
    if current_user.role == 'agente' and email.agente_id != current_user.id:
        flash("Acesso não permitido.", "danger")
        return redirect(url_for('routes.emails'))

    if email.status == 'nao_lido':
        email.status = 'lido'
        db.session.commit()

    return render_template("ver_email.html", 
                           page_title=f"Email: {email.assunto}",
                           email=email)

@bp.route("/emails/agente/<int:agente_id>/alertar")
@login_required
def alertar_agente(agente_id):
    from . import socketio
    
    if current_user.role != 'admin_empresa':
        flash("Apenas administradores podem enviar alertas.", "danger")
        return redirect(url_for('routes.dashboard'))

    agente = Usuario.query.filter_by(id=agente_id, empresa_id=current_user.empresa_id).first_or_404()
    assunto_email = request.args.get('assunto', '[Assunto não especificado]')
    
    mensagem = f"ALERTA DO SEU GESTOR: Por favor, verifique o email com o assunto '{assunto_email}' com prioridade."

    nova_notificacao = Notificacao(
        usuario_id=agente.id,
        remetente_nome=current_user.nome,
        mensagem=mensagem
    )
    db.session.add(nova_notificacao)
    db.session.commit()

    socketio.emit('nova_notificacao', {'remetente': current_user.nome, 'mensagem': mensagem}, room=str(agente.id))
    
    flash(f"Alerta sobre o email '{assunto_email}' enviado para {agente.nome}.", "info")
    return redirect(url_for('routes.caixa_email_agente', agente_id=agente.id))

@bp.route('/notificacoes/nao_lidas')
@login_required
def get_notificacoes_nao_lidas():
    notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).order_by(Notificacao.created_at.desc()).all()
    resultado = [
        {'id': n.id, 'mensagem': n.mensagem, 'remetente': n.remetente_nome} 
        for n in notificacoes
    ]
    return jsonify(resultado)

@bp.route('/notificacoes/marcar_como_lidas', methods=['POST'])
@login_required
def marcar_como_lidas():
    try:
        Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({'lida': True})
        db.session.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route("/whatsapp_dashboard")
@login_required
def whatsapp_dashboard():
    """Exibe o dashboard de produtividade do WhatsApp."""
    if current_user.role == 'super_admin':
        return redirect(url_for('admin.dashboard'))
    
    return render_template("whatsapp_dashboard.html")

@bp.route("/produtividade/agente/<int:agente_id>")
@login_required
def produtividade_agente(agente_id):
    if current_user.role != 'admin_empresa':
        flash("Acesso não permitido.", "danger")
        return redirect(url_for('routes.whatsapp_dashboard'))

    agente = Usuario.query.get_or_404(agente_id)
    if agente.empresa_id != current_user.empresa_id:
        flash("Agente não encontrado.", "danger")
        return redirect(url_for('routes.whatsapp_dashboard'))

    return render_template("produtividade_agente.html", agente=agente)

@bp.route("/productivity/monitoring")
@login_required
@require_plan('completo')
def productivity_monitoring():
    if current_user.role != 'admin_empresa':
        flash("Acesso não permitido.", "danger")
        return redirect(url_for('routes.dashboard'))

    agents = Usuario.query.filter(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.role.in_(['agente', 'admin_empresa'])
    ).order_by(Usuario.nome).all()

    return render_template("productivity_monitoring.html", agents=agents, page_title="Monitoramento de Agentes")

@bp.route("/productivity/agent/<int:agente_id>/log")
@login_required
@require_plan('completo')
def productivity_agent_log(agente_id):
    if current_user.role != 'admin_empresa':
        flash("Acesso não permitido.", "danger")
        return redirect(url_for('routes.dashboard'))

    agente = Usuario.query.get_or_404(agente_id)
    if agente.empresa_id != current_user.empresa_id:
        flash("Agente não encontrado.", "danger")
        return redirect(url_for('routes.productivity_monitoring'))

    logs = ActivityLog.query.filter_by(
        usuario_id=agente.id
    ).order_by(ActivityLog.timestamp.desc()).all()

    return render_template(
        "productivity_log.html",
        agente=agente,
        logs=logs,
        page_title=f"Histórico de Atividade de {agente.nome}"
    )

# --- NOVA ROTA PARA GERAR O TOKEN ---
@bp.route('/desktop_agent/generate_token', methods=['POST'])
@login_required
def generate_desktop_token():
    # Apenas agentes e admins da empresa podem gerar tokens
    if current_user.role not in ['agente', 'admin_empresa']:
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403

    token = current_user.generate_desktop_token()
    return jsonify({'status': 'success', 'token': token})