# call_center_project/app/api.py

from flask import Blueprint, request, jsonify, current_app
from .models import db, Avaliacao, ConversaWhatsApp, MensagemWhatsApp, Empresa, Usuario
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
import requests
import json
from .admin import admin_required
from . import socketio

bp = Blueprint('api', __name__, url_prefix='/api')

# --- ROTAS PARA O CHAT DE WHATSAPP ---

@bp.route('/conversa/<int:conversa_id>')
@login_required
def get_conversa(conversa_id):
    """Busca o histórico de mensagens de uma conversa específica."""
    conversa = ConversaWhatsApp.query.filter_by(id=conversa_id, empresa_id=current_user.empresa_id).first_or_404()
    
    mensagens = [
        {
            'remetente': msg.remetente,
            'conteudo': msg.conteudo,
            'timestamp': msg.timestamp.strftime('%H:%M')
        } for msg in conversa.mensagens
    ]
    
    return jsonify({
        'cliente': conversa.nome_cliente,
        'mensagens': mensagens
    })

@bp.route('/conversa/<int:conversa_id>/enviar', methods=['POST'])
@login_required
def enviar_mensagem_conversa(conversa_id):
    """Envia uma mensagem de um agente para um cliente."""
    conversa = ConversaWhatsApp.query.filter_by(id=conversa_id, empresa_id=current_user.empresa_id).first_or_404()
    data = request.json
    conteudo_mensagem = data.get('mensagem')

    if not conteudo_mensagem:
        return jsonify({'status': 'error', 'message': 'A mensagem não pode estar vazia.'}), 400

    # Lógica para enviar a mensagem através da API do WhatsApp (usando a função de services)
    # from .services import enviar_mensagem_whatsapp
    # sucesso = enviar_mensagem_whatsapp(conversa.wa_id, conteudo_mensagem, conversa.empresa)
    
    # Por agora, vamos simular o sucesso
    sucesso = True 

    if sucesso:
        # Salva a mensagem do agente na base de dados
        nova_mensagem = MensagemWhatsApp(
            conversa_id=conversa.id,
            remetente='agente',
            conteudo=conteudo_mensagem,
            empresa_id=current_user.empresa_id
        )
        db.session.add(nova_mensagem)
        db.session.commit()
        return jsonify({'status': 'ok', 'message': 'Mensagem enviada com sucesso.'})
    else:
        return jsonify({'status': 'error', 'message': 'Falha ao enviar a mensagem pelo provedor.'}), 500


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
    timestamp = datetime.fromtimestamp(int(message['timestamp']))

    conversa = ConversaWhatsApp.query.filter_by(wa_id=wa_id, empresa_id=empresa.id).first()
    
    if not conversa:
        conversa = ConversaWhatsApp(wa_id=wa_id, nome_cliente=f"Cliente {wa_id[-4:]}", status='pendente', empresa_id=empresa.id)
        db.session.add(conversa)
        db.session.flush()

    nova_mensagem = MensagemWhatsApp(
        conversa_id=conversa.id,
        remetente='cliente',
        conteudo=conteudo,
        timestamp=timestamp,
        empresa_id=empresa.id
    )
    db.session.add(nova_mensagem)
    db.session.commit()
    
    # Emite a nova mensagem para a sala da conversa
    socketio.emit('nova_mensagem_cliente', {
        'conversa_id': conversa.id,
        'conteudo': conteudo,
        'timestamp': timestamp.strftime('%H:%M')
    }, room=f"conversa_{conversa.id}")

def enviar_mensagem_whatsapp(wa_id, mensagem, empresa):
    # ... (código inalterado)
    pass

@bp.route("/registro_chamada", methods=["POST"])
def registro_chamada():
    return jsonify({"status": "ok", "message": "Rota em desenvolvimento."}), 501