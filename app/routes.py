# call_center_project/app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from .models import db, Avaliacao, ConversaWhatsApp, Usuario
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import random

bp = Blueprint('routes', __name__)

@bp.route("/")
@login_required
def index():
    # Simplificado: o login já redireciona para o sítio certo.
    # Esta rota agora só serve de fallback se alguém a aceder diretamente.
    if current_user.role == 'super_admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for("routes.dashboard"))

@bp.route("/dashboard")
@login_required
def dashboard():
    # A verificação do super_admin foi removida, pois ele nunca chegará aqui.
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

# --- O resto do ficheiro permanece o mesmo ---

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

    # Lógica para mostrar apenas conversas atribuídas ao agente
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