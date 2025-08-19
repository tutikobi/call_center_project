# call_center_project/app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from .models import db, Avaliacao, ConversaWhatsApp, Usuario, Notificacao
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
import random
# A importação 'from . import socketio' foi REMOVIDA do topo do ficheiro

bp = Blueprint('routes', __name__)

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
    csat_geral = db.session.query(func.avg(Avaliacao.csat)).filter_by(empresa_id=empresa_id_do_usuario).scalar() or 0
    agentes_online = Usuario.query.filter_by(empresa_id=empresa_id_do_usuario).limit(5).all()
    
    return render_template("dashboard.html", 
                         total_avaliacoes=total_avaliacoes,
                         conversas_ativas=conversas_ativas,
                         csat_geral=round(csat_geral, 1),
                         agentes_online=agentes_online)

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
    if current_user.empresa.plano not in ['medio', 'pro', 'premium']:
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

    hoje = datetime.utcnow().date()
    emails_recebidos_hoje = random.randint(15, 30)
    emails_respondidos = random.randint(5, emails_recebidos_hoje)
    emails_nao_lidos = random.randint(3, 10)
    
    lista_de_emails = [
        {'remetente': 'cliente1@example.com', 'assunto': 'Dúvida sobre o contrato 123', 'status': 'nao_lido'},
        {'remetente': 'fornecedor@example.com', 'assunto': 'Proposta de parceria', 'status': 'lido'},
        {'remetente': 'cliente2@example.com', 'assunto': 'Re: Problema com a fatura', 'status': 'respondido'},
        {'remetente': 'cliente3@example.com', 'assunto': 'URGENTE: Ajuda necessária', 'status': 'nao_lido'},
    ]

    return render_template("caixa_email_agente.html", 
                           page_title=f"Caixa de Entrada de {agente.nome}",
                           agente=agente,
                           emails_recebidos_hoje=emails_recebidos_hoje,
                           emails_respondidos=emails_respondidos,
                           emails_nao_lidos=emails_nao_lidos,
                           lista_de_emails=lista_de_emails)

@bp.route("/emails/agente/<int:agente_id>/alertar")
@login_required
def alertar_agente(agente_id):
    from . import socketio # --- IMPORTAÇÃO MOVIDA PARA AQUI ---
    
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

    socketio.emit('nova_notificacao', {'mensagem': mensagem}, room=str(agente.id))
    
    flash(f"Alerta sobre o email '{assunto_email}' enviado para {agente.nome}.", "info")
    return redirect(url_for('routes.caixa_email_agente', agente_id=agente.id))

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
                query = query.filter(Avaliacao.data >= data_inicio)
            except ValueError:
                pass 
        if canal and canal != 'todos':
            query = query.filter_by(canal=canal)
        if agente_id and agente_id != 'todos':
            query = query.filter_by(agente_id=int(agente_id))
        dados_relatorio = query.order_by(Avaliacao.data.desc()).all()
    return render_template("relatorios.html", 
        agentes=agentes, 
        dados_relatorio=dados_relatorio,
        filtros=filtros_aplicados
    )