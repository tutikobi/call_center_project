# call_center_project/app/events.py

from flask_socketio import emit, join_room
from flask_login import current_user
from . import socketio

@socketio.on('connect')
def handle_connect():
    """Quando um utilizador se conecta, ele entra numa 'sala' privada."""
    if current_user.is_authenticated:
        # Cada utilizador entra numa sala com o nome do seu próprio ID.
        # Isto permite-nos enviar mensagens apenas para ele.
        join_room(str(current_user.id))
        print(f'Cliente {current_user.nome} conectado e entrou na sala {current_user.id}')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')