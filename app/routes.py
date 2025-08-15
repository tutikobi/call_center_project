# call_center_project/app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from .models import db, Avaliacao, ConversaWhatsApp, Usuario
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import random

bp = Blueprint('routes', __name__)

# ... (rotas index, dashboard) ...
@bp.route("/")
@login_required
def index():
    return redirect(url_for("routes.dashboard"))

@bp.route("/dashboard")
@login_required
def dashboard():
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

# --- ROTA DE AVALIAÇÃO ATUALIZADA ---
@bp.route("/avaliar", methods=["GET", "POST"])
@login_required
def avaliar():
    # Busca todos os usuários (agentes e admins) da empresa do usuário logado
    agentes_da_empresa = Usuario.query.filter_by(empresa_id=current_user.empresa_id).order_by(Usuario.nome).all()

    if request.method == "POST":
        agente_selecionado_id = request.form.get("agente_id")
        
        # Validação para garantir que um agente foi selecionado
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
    
    # No método GET, apenas renderiza a página passando a lista de agentes
    return render_template("avaliar.html", agentes=agentes_da_empresa)

# ... (resto do arquivo routes.py) ...
@bp.route("/conversas")
@login_required
def conversas():
    conversas_ativas = ConversaWhatsApp.query.filter_by(
        empresa_id=current_user.empresa_id,
        status='ativo'
    ).order_by(ConversaWhatsApp.inicio.desc()).all()
    return render_template("conversas.html", conversas=conversas_ativas)

@bp.route("/populate_demo_data")
@login_required
def populate_demo_data():
    empresa_id = current_user.empresa_id
    agentes_da_empresa = Usuario.query.filter_by(empresa_id=empresa_id).all()
    if not agentes_da_empresa:
        flash("Sua empresa não tem agentes para associar às avaliações.", "warning")
        return redirect(url_for('routes.dashboard'))
    for _ in range(20):
        agente_aleatorio = random.choice(agentes_da_empresa)
        avaliacao = Avaliacao(
            agente_id=agente_aleatorio.id,
            empresa_id=empresa_id,
            canal=random.choice(['whatsapp', 'voz', 'email']),
            csat=random.uniform(3.0, 5.0)
        )
        db.session.add(avaliacao)
    db.session.commit()
    flash("20 avaliações de teste foram criadas com sucesso para sua empresa!", "success")
    return redirect(url_for('routes.dashboard'))

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
        if periodo:
            try:
                dias = int(periodo)
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

@bp.route("/api_docs")
@login_required
def api_docs():
    return render_template("api_docs.html")
