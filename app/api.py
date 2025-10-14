# call_center_project/app/api.py

from flask import Blueprint, request, jsonify, current_app
from .models import db, Avaliacao, ConversaWhatsApp, MensagemWhatsApp, Empresa, Usuario
from app.models_rh import Funcionario, Departamento
from app.rh.calculos import calcular_folha_pagamento
from flask_login import login_required, current_user
from datetime import datetime, time
from sqlalchemy import func, cast, Date, desc
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

    sucesso = True 

    if sucesso:
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
    
    socketio.emit('nova_mensagem_cliente', {
        'conversa_id': conversa.id,
        'conteudo': conteudo,
        'timestamp': timestamp.strftime('%H:%M')
    }, room=f"conversa_{conversa.id}")
    
    socketio.emit('atualizar_dashboard')


def enviar_mensagem_whatsapp(wa_id, mensagem, empresa):
    pass

@bp.route("/registro_chamada", methods=["POST"])
def registro_chamada():
    return jsonify({"status": "ok", "message": "Rota em desenvolvimento."}), 501

@bp.route("/dashboard/produtividade")
@login_required
def dados_produtividade():
    empresa_id = current_user.empresa_id
    hoje = datetime.utcnow().date()
    
    total_atendimentos = ConversaWhatsApp.query.filter(
        ConversaWhatsApp.empresa_id == empresa_id,
        cast(ConversaWhatsApp.created_at, Date) == hoje
    ).count()
    
    tma_query = db.session.query(
        func.avg(func.extract('epoch', ConversaWhatsApp.fim - ConversaWhatsApp.inicio))
    ).filter(
        ConversaWhatsApp.empresa_id == empresa_id,
        ConversaWhatsApp.fim.isnot(None),
        cast(ConversaWhatsApp.fim, Date) == hoje
    ).scalar() or 0
    tma_minutos = int(tma_query // 60)
    tma_segundos = int(tma_query % 60)
    tma_formatado = f"{tma_minutos:02d}:{tma_segundos:02d}"
    
    fila_query = ConversaWhatsApp.query.filter(
        ConversaWhatsApp.empresa_id == empresa_id,
        ConversaWhatsApp.agente_atribuido_id.is_(None),
        ConversaWhatsApp.status == 'ativo'
    ).order_by(ConversaWhatsApp.created_at.asc()).all()
    
    fila = [
        {
            "assunto": c.assunto,
            "cliente": c.nome_cliente,
            "tempo": c.created_at.strftime('%H:%M'),
            "status": "Aguardando"
        } for c in fila_query
    ]
    
    csat_geral = db.session.query(func.avg(Avaliacao.csat)).filter(
        Avaliacao.empresa_id == empresa_id
    ).scalar() or 0.0
    
    agentes_query = Usuario.query.filter(
        Usuario.empresa_id == empresa_id,
        Usuario.role.in_(['agente', 'admin_empresa'])
    )

    agentes = []
    for agente in agentes_query.all():
        atendimentos_hoje = ConversaWhatsApp.query.filter(
            ConversaWhatsApp.agente_atribuido_id == agente.id,
            cast(ConversaWhatsApp.created_at, Date) == hoje
        ).count()
        
        agente_tma_query = db.session.query(
            func.avg(func.extract('epoch', ConversaWhatsApp.fim - ConversaWhatsApp.inicio))
        ).filter(
            ConversaWhatsApp.agente_atribuido_id == agente.id,
            ConversaWhatsApp.fim.isnot(None),
            cast(ConversaWhatsApp.fim, Date) == hoje
        ).scalar() or 0
        agente_tma_min = int(agente_tma_query // 60)
        agente_tma_sec = int(agente_tma_query % 60)

        top_assuntos_query = db.session.query(
            ConversaWhatsApp.assunto, func.count(ConversaWhatsApp.id).label('total')
        ).filter(
            ConversaWhatsApp.agente_atribuido_id == agente.id,
            cast(ConversaWhatsApp.created_at, Date) == hoje
        ).group_by(ConversaWhatsApp.assunto).order_by(func.count(ConversaWhatsApp.id).desc()).limit(5).all()

        top_assuntos = [{"assunto": a.assunto, "total": a.total} for a in top_assuntos_query]
        
        agentes.append({
            "id": agente.id,
            "nome": agente.nome,
            "setor": agente.departamento.nome if agente.departamento else "Sem Setor",
            "atendimentos": atendimentos_hoje,
            "tma": f"{agente_tma_min:02d}:{agente_tma_sec:02d}",
            "status": agente.status_agente,
            "top_assuntos": top_assuntos
        })
    
    return jsonify({
        "totalAtendimentos": total_atendimentos,
        "tma": tma_formatado,
        "fila": fila,
        "csatGeral": round(csat_geral, 1),
        "agentes": agentes
    })

@bp.route('/rh/dados_dashboard_financeiro')
@login_required
def dados_dashboard_financeiro():
    empresa_id = current_user.empresa_id
    funcionarios_ativos = Funcionario.query.filter_by(empresa_id=empresa_id, status='ativo').all()

    if not funcionarios_ativos:
        return jsonify({
            "total_funcionarios": 0, "custo_total_empresa": 0,
            "total_salarios_liquidos": 0, "total_beneficios": 0,
            "total_impostos": 0, "distribuicao_custos": {'labels': [], 'data': []}
        })

    custo_total = 0
    salarios_liquidos = 0
    beneficios = 0
    impostos = 0
    
    for func in funcionarios_ativos:
        resultado = calcular_folha_pagamento(func)
        if resultado['success']:
            custo_total += resultado['totais']['custo_total_empresa']
            salarios_liquidos += resultado['totais']['liquido_funcionario']
            beneficios += resultado['proventos']['vale_alimentacao'] + resultado['proventos']['vale_refeicao']
            impostos += resultado['custos_empresa']['fgts'] + resultado['custos_empresa']['inss_patronal']

    distribuicao_custos = {
        'labels': ['Salários Líquidos', 'Benefícios (VA/VR)', 'Impostos (FGTS/INSS Patronal)'],
        'data': [
            round(float(salarios_liquidos), 2),
            round(float(beneficios), 2),
            round(float(impostos), 2)
        ]
    }
    
    return jsonify({
        "total_funcionarios": len(funcionarios_ativos),
        "custo_total_empresa": round(float(custo_total), 2),
        "total_salarios_liquidos": round(float(salarios_liquidos), 2),
        "total_beneficios": round(float(beneficios), 2),
        "total_impostos": round(float(impostos), 2),
        "distribuicao_custos": distribuicao_custos
    })


@bp.route('/agente/mudar_status', methods=['POST'])
@login_required
def mudar_status_agente():
    novo_status = request.json.get('status')
    if not novo_status:
        return jsonify({'status': 'error', 'message': 'Status não fornecido.'}), 400
    
    agente = Usuario.query.get(current_user.id)
    agente.status_agente = novo_status
    db.session.commit()
    
    socketio.emit('atualizar_dashboard')
    
    return jsonify({'status': 'ok', 'message': f'Status alterado para {novo_status}.'})

@bp.route('/conversa/<int:conversa_id>/definir_assunto', methods=['POST'])
@login_required
def definir_assunto_conversa(conversa_id):
    novo_assunto = request.json.get('assunto')
    if not novo_assunto:
        return jsonify({'status': 'error', 'message': 'Assunto não fornecido.'}), 400
        
    conversa = ConversaWhatsApp.query.get_or_404(conversa_id)
    if conversa.empresa_id != current_user.empresa_id:
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403
        
    conversa.assunto = novo_assunto
    db.session.commit()
    
    socketio.emit('atualizar_dashboard')
    
    return jsonify({'status': 'ok', 'message': f'Assunto da conversa alterado para {novo_assunto}.'})
# ... (todo o seu código existente do api.py) ...

# --- NOVAS ROTAS DE PRODUTIVIDADE (ADICIONAR NO FINAL) ---
from app.decorators import agent_api_key_required
from app.models import ActivityLog, ProductivityRules
from app.services.ai_productivity_service import ai_productivity_service
from app.services.realtime_service import notify_dashboard_update
from flask import g

@bp.route('/productivity/log', methods=['POST'])
@agent_api_key_required
def log_activity():
    data = request.json; agent_user = g.current_user
    rules = ProductivityRules.query.filter_by(empresa_id=agent_user.empresa_id).first()
    rules_dict = {"process_rules": rules.process_rules if rules else [], "url_rules": rules.url_rules if rules else [], "custom_ai_prompt": rules.custom_ai_prompt if rules else None}
    analysis = ai_productivity_service.analyze_activity(data, rules_dict)
    new_log = ActivityLog(usuario_id=agent_user.id, empresa_id=agent_user.empresa_id, timestamp=datetime.fromisoformat(data['timestamp']), window_title=data.get('window_title'), process_name=data.get('process_name'), url=data.get('url'), is_productive=analysis.get('is_productive'), category=analysis.get('category'), ai_analysis=analysis)
    db.session.add(new_log); db.session.commit()
    realtime_data = { "usuario_id": agent_user.id, "usuario_nome": agent_user.nome, **analysis }
    notify_dashboard_update(agent_user.empresa_id, realtime_data)
    return jsonify({"status": "success"}), 201

@bp.route('/productivity/rules', methods=['GET', 'POST'])
@login_required
def manage_rules():
    if current_user.role != 'admin_empresa': return jsonify({"error": "Acesso não autorizado."}), 403
    rules = ProductivityRules.query.filter_by(empresa_id=current_user.empresa_id).first()
    if not rules: rules = ProductivityRules(empresa_id=current_user.empresa_id); db.session.add(rules)
    if request.method == 'POST':
        data = request.json
        rules.process_rules = data.get('process_rules', [])
        rules.url_rules = data.get('url_rules', [])
        rules.custom_ai_prompt = data.get('custom_ai_prompt')
        db.session.commit()
        return jsonify({"message": "Regras atualizadas."})
    return jsonify({"process_rules": rules.process_rules or [], "url_rules": rules.url_rules or [], "custom_ai_prompt": rules.custom_ai_prompt or ""})
