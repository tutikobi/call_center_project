# call_center_project/app/api.py

from flask import Blueprint, request, jsonify, current_app
from .models import db, Avaliacao, ConversaWhatsApp, MensagemWhatsApp, Empresa, Usuario
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
import requests
import json
from .admin import admin_required # Importa o decorator do admin para proteger a rota

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route("/dados_dashboard_graficos")
@login_required
def dados_dashboard_graficos():
    empresa_id_do_usuario = current_user.empresa_id

    # 1. Gráfico de Atendimentos por Canal
    atendimentos_por_canal = db.session.query(
        Avaliacao.canal, func.count(Avaliacao.id)
    ).filter(Avaliacao.empresa_id == empresa_id_do_usuario).group_by(Avaliacao.canal).all()
    
    dados_canal = {
        'labels': [item[0] for item in atendimentos_por_canal],
        'data': [item[1] for item in atendimentos_por_canal]
    }

    # 2. Gráfico de CSAT Médio por Agente
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

# --- NOVA ROTA DE API PARA O DASHBOARD DO ADMIN ---
@bp.route("/dados_admin_dashboard")
@login_required
@admin_required
def dados_admin_dashboard():
    # Busca o número de empresas ativas e bloqueadas, excluindo a empresa do sistema
    ativas = Empresa.query.filter(Empresa.status_assinatura == 'ativa', Empresa.nome_empresa != "Sistema Call Center").count()
    bloqueadas = Empresa.query.filter(Empresa.status_assinatura == 'bloqueada', Empresa.nome_empresa != "Sistema Call Center").count()

    dados_grafico = {
        'labels': ['Ativas', 'Bloqueadas'],
        'data': [ativas, bloqueadas]
    }

    return jsonify({'graficoEmpresas': dados_grafico})


@bp.route("/webhook/<int:empresa_id>", methods=["GET", "POST"])
def webhook_whatsapp(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        if verify_token and verify_token == empresa.webhook_verify_token:
            return request.args.get("hub.challenge")
        return "Token de verificação inválido", 403
    data = request.json
    if data.get("object") == "whatsapp_business_account":
        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if "messages" in change.get("value", {}):
                        for message in change["value"]["messages"]:
                            processar_mensagem_recebida(message, empresa)
        except (KeyError, IndexError) as e:
            current_app.logger.error(f"Erro ao processar payload do webhook para empresa {empresa.id}: {e}")
            pass
    return jsonify({"status": "ok"}), 200

def processar_mensagem_recebida(message, empresa):
    wa_id = message["from"]
    conteudo = message["text"]["body"] if "text" in message else "Mídia recebida"
    conversa = ConversaWhatsApp.query.filter_by(wa_id=wa_id, empresa_id=empresa.id, status='ativo').first()
    if not conversa:
        conversa = ConversaWhatsApp(
            wa_id=wa_id,
            nome_cliente=f"Cliente {wa_id[-4:]}",
            status='ativo',
            empresa_id=empresa.id
        )
        db.session.add(conversa)
        db.session.flush()
    nova_mensagem = MensagemWhatsApp(conversa_id=conversa.id, remetente='cliente', conteudo=conteudo, empresa_id=empresa.id)
    db.session.add(nova_mensagem)
    db.session.commit()

def enviar_mensagem_whatsapp(wa_id, mensagem, empresa):
    if not all([empresa.whatsapp_token, empresa.whatsapp_number_id]):
        current_app.logger.error(f"ERRO: Tentativa de enviar mensagem pela empresa {empresa.id} sem credenciais.")
        return {"error": "Credenciais da API não configuradas."}
    headers = {"Authorization": f"Bearer {empresa.whatsapp_token}", "Content-Type": "application/json"}
    url = f"https://graph.facebook.com/v17.0/{empresa.whatsapp_number_id}/messages"
    payload = {"messaging_product": "whatsapp", "to": wa_id, "type": "text", "text": {"body": mensagem}}
    try:
        response = requests.post(url, headers=headers, json=payload )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Falha ao enviar mensagem para {wa_id} pela empresa {empresa.id}: {e}")
        return {"error": str(e)}

@bp.route("/registro_chamada", methods=["POST"])
def registro_chamada():
    return jsonify({"status": "ok", "message": "Rota em desenvolvimento."}), 501

@bp.route("/enviar_mensagem", methods=["POST"])
def api_enviar_mensagem():
    return jsonify({"status": "ok", "message": "Rota em desenvolvimento."}), 501