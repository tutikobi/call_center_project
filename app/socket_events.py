# call_center_project/app/events.py

from flask_socketio import emit, join_room
from flask_login import current_user
from . import socketio

@socketio.on('connect')
def handle_connect():
    """Quando um utilizador se conecta, ele entra numa 'sala' privada."""
    if current_user.is_authenticated:
        join_room(str(current_user.id))
        print(f'Cliente {current_user.nome} conectado e entrou na sala {current_user.id}')

# --- NOVO EVENTO PARA SE JUNTAR A UMA CONVERSA ESPECÍFICA ---
@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Quando um agente abre um chat, ele entra na sala dessa conversa."""
    conversa_id = data.get('conversa_id')
    if conversa_id:
        join_room(f"conversa_{conversa_id}")
        print(f"Agente {current_user.nome} entrou na sala da conversa {conversa_id}")


@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')