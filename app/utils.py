# call_center_project/app/utils.py

from flask import Blueprint, jsonify
from .models import db, Avaliacao, ConversaWhatsApp, MensagemWhatsApp
import random
from datetime import datetime

bp = Blueprint('utils', __name__)

@bp.route("/populate_demo")
def populate_demo():
    """Popula o banco com dados de demonstração."""
    # Limpa dados antigos para evitar duplicatas
    db.session.query(MensagemWhatsApp).delete()
    db.session.query(ConversaWhatsApp).delete()
    db.session.query(Avaliacao).delete()
    db.session.commit()

    agentes = ["Maria Silva", "João Santos", "Ana Costa", "Pedro Lima"]
    
    # Avaliações de Voz
    for _ in range(20):
        db.session.add(Avaliacao(
            agente=random.choice(agentes), canal="voz",
            chamada_id=f"CALL_{random.randint(10000,99999)}",
            csat=random.uniform(3.0, 5.0), nps=random.randint(6, 10)
        ))

    # Conversas e Avaliações de WhatsApp
    for i in range(15):
        conversa = ConversaWhatsApp(
            wa_id=f"55119{random.randint(10000000, 99999999)}",
            nome_cliente=f"Cliente Demo {i+1}",
            agente=random.choice(agentes), status='ativo'
        )
        db.session.add(conversa)
        db.session.flush()

        for j in range(random.randint(3, 10)):
            db.session.add(MensagemWhatsApp(
                conversa_id=conversa.id,
                remetente=random.choice(['cliente', 'agente']),
                conteudo=f"Mensagem de teste {j+1}"
            ))
        
        db.session.add(Avaliacao(
            agente=conversa.agente, canal="whatsapp",
            chamada_id=f"WA_{conversa.wa_id}",
            csat=random.uniform(3.5, 5.0), nps=random.randint(7, 10)
        ))

    db.session.commit()
    return jsonify({"status": "ok", "message": "Banco de dados populado com sucesso!"})
