# call_center_project/app/socket_events.py

from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from . import socketio

@socketio.on('connect')
def handle_connect():
    """
    Quando um usuário se conecta, ele entra em duas salas:
    1. Uma sala pessoal para notificações diretas.
    2. Uma sala da empresa para receber atualizações de toda a equipe.
    """
    if current_user.is_authenticated:
        # Sala pessoal
        join_room(str(current_user.id))
        print(f'Cliente {current_user.nome} conectado e entrou na sala pessoal {current_user.id}')
        
        # Sala da empresa
        if hasattr(current_user, 'empresa_id') and current_user.empresa_id:
            empresa_room = f'empresa_{current_user.empresa_id}'
            join_room(empresa_room)
            print(f'Cliente {current_user.nome} também entrou na sala da empresa {empresa_room}')

@socketio.on('disconnect')
def handle_disconnect():
    """Quando o usuário desconecta, ele sai das salas."""
    if current_user.is_authenticated:
        leave_room(str(current_user.id))
        if hasattr(current_user, 'empresa_id') and current_user.empresa_id:
            leave_room(f'empresa_{current_user.empresa_id}')
    print('Cliente desconectado')

# O evento 'join_conversation' pode ser mantido se você ainda o usa
@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Quando um agente abre um chat, ele entra na sala dessa conversa."""
    conversa_id = data.get('conversa_id')
    if conversa_id:
        join_room(f"conversa_{conversa_id}")
        print(f"Agente {current_user.nome} entrou na sala da conversa {conversa_id}")
