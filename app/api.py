# call_center_project/app/api.py

from flask import Blueprint, request, jsonify, current_app
from .models import db, Avaliacao, ConversaWhatsApp, MensagemWhatsApp, Empresa, Usuario, Email
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
import requests
import json
from .admin import admin_required

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route("/dados_dashboard_graficos")
@login_required
def dados_dashboard_graficos():
    empresa_id_do_usuario = current_user.empresa_id

    atendimentos_por_canal = db.session.query(
        Avaliacao.canal, func.count(Avaliacao.id)
    ).filter(Avaliacao.empresa_id == empresa_id_do_usuario).group_by(Avaliacao.canal).all()
    
    dados_canal = {
        'labels': [item[0] for item in atendimentos_por_canal],
        'data': [item[1] for item in atendimentos_por_canal]
    }

    csat_por_agente = db.session.query(
        Usuario.nome, func.avg(Avaliacao.csat)
    ).join(Usuario, Avaliacao.agente_id == Usuario.id)\
     .filter(Avaliacao.empresa_id == empresa_id_do_usuario)\
     .group_by(Usuario.nome).order_by(func.avg(Avaliacao.csat).desc()).all()

    dados_csat_agente = {
        'labels': [item[0] for item in csat_por_agente],
        'data': [round(item[1] or 0, 2) for item in csat_por_agente]
    }

    return jsonify({
        'graficoCanais': dados_canal,
        'graficoCsatAgente': dados_csat_agente
    })

@bp.route("/dados_admin_dashboard")
@login_required
@admin_required
def dados_admin_dashboard():
    ativas = Empresa.query.filter(Empresa.status_assinatura == 'ativa', Empresa.nome_empresa != "Sistema Call Center").count()
    bloqueadas = Empresa.query.filter(Empresa.status_assinatura == 'bloqueada', Empresa.nome_empresa != "Sistema Call Center").count()
    dados_grafico = {
        'labels': ['Ativas', 'Bloqueadas'],
        'data': [ativas, bloqueadas]
    }
    return jsonify({'graficoEmpresas': dados_grafico})


# --- ROTA PARA RECEBER EMAILS ENCAMINHADOS (WEBHOOK) ---
@bp.route("/webhook/email", methods=["POST"])
def email_webhook():
    # Os serviços de webhook (SendGrid, Mailgun) enviam os dados do email como um formulário
    data = request.form
    
    # Extrai as informações principais
    # A estrutura exata (ex: 'sender', 'subject') pode variar um pouco dependendo do serviço
    remetente = data.get('from')
    destinatario = data.get('to')
    assunto = data.get('subject')
    corpo = data.get('text') # Corpo em texto simples
    
    if not all([remetente, destinatario, assunto, corpo]):
        # Se faltar alguma informação essencial, retorna um erro.
        return jsonify({'status': 'error', 'message': 'Dados do email incompletos.'}), 400

    try:
        # Lógica para encontrar a empresa associada a este email
        # Aqui, estamos a assumir que o email foi enviado para algo como "empresa_X@receber.seusistema.com"
        # Esta lógica precisará de ser adaptada à sua configuração.
        # Por agora, vamos assumir que encontramos uma empresa de exemplo.
        empresa = Empresa.query.first() # Lógica de exemplo!
        if not empresa:
            raise Exception("Nenhuma empresa encontrada para associar o email.")

        # Lógica para atribuir o email a um agente (ex: o primeiro agente da empresa)
        agente_destino = Usuario.query.filter_by(empresa_id=empresa.id, role='agente').first()
        agente_id = agente_destino.id if agente_destino else None

        # Cria o novo registo de email na base de dados
        novo_email = Email(
            empresa_id=empresa.id,
            agente_id=agente_id,
            remetente=remetente,
            assunto=assunto,
            corpo=corpo,
            status='nao_lido'
        )
        db.session.add(novo_email)
        db.session.commit()
        
        # (Opcional) Enviar uma notificação em tempo real para o agente
        # from . import socketio
        # if agente_id:
        #     socketio.emit('novo_email', {'assunto': assunto}, room=str(agente_id))

        print(f"Email de '{remetente}' com assunto '{assunto}' recebido e guardado com sucesso.")
        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao processar webhook de email: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/webhook/<int:empresa_id>", methods=["GET", "POST"])
def webhook_whatsapp(empresa_id):
    # ... (código inalterado)
    return jsonify({"status": "ok"}), 200

# ... (outras rotas da API inalteradas)