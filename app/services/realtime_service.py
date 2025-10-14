# call_center_project/app/services/realtime_service.py
from app import socketio

def notify_dashboard_update(empresa_id: int, data: dict):
    """Envia uma notificação via WebSocket para a sala da empresa."""
    room_name = f'empresa_{empresa_id}'
    socketio.emit('productivity_update', data, room=room_name)