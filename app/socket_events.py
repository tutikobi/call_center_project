# call_center_project/app/socket_events.py

from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request, current_app
from . import socketio
from datetime import datetime

# --- Rastreamento de Status ---
# ATENÇÃO: Usar dicionários globais NÃO é ideal para produção com múltiplos workers.
# Em produção, substitua por Redis ou outra solução de memória compartilhada.
# Exemplo com Redis (requer pip install redis):
# from redis import Redis
# redis_client = Redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379'))
# def set_user_web_status(user_id, status): redis_client.hset('web_status', str(user_id), 'online' if status else 'offline')
# def get_user_web_status(user_id): return redis_client.hget('web_status', str(user_id)) == b'online'
# def set_desktop_status(agent_id, monitoring, last_seen): redis_client.hset(f'desktop_status:{agent_id}', mapping={'monitoring': '1' if monitoring else '0', 'last_seen': last_seen.isoformat()})
# def get_desktop_status(agent_id): data = redis_client.hgetall(f'desktop_status:{agent_id}'); return {'monitoring': data.get(b'monitoring') == b'1', 'last_seen': datetime.fromisoformat(data[b'last_seen'].decode()) if b'last_seen' in data else None}

# --- Implementação com Dicionário Simples (para desenvolvimento) ---
online_users_web_sids = {} # {user_id: set(sid1, sid2), ...}
agent_desktop_status = {}  # {agent_id: {'monitoring': True/False, 'last_seen': datetime}}

def get_user_web_status(user_id):
    """Verifica se o usuário tem alguma sessão web ativa."""
    return user_id in online_users_web_sids and len(online_users_web_sids[user_id]) > 0

def get_desktop_status(agent_id):
    """Obtém o último status conhecido do desktop agent."""
    return agent_desktop_status.get(agent_id, {'monitoring': False, 'last_seen': None})
# --- Fim Rastreamento de Status ---


def broadcast_agent_status(user_id, empresa_id):
    """Envia o status combinado (web e desktop) para os admins da empresa."""
    is_online_web = get_user_web_status(user_id)
    desktop_info = get_desktop_status(user_id)
    is_monitoring = desktop_info.get('monitoring', False)
    last_seen_desktop = desktop_info.get('last_seen')

    status_data = {
        'agent_id': user_id,
        'is_online_web': is_online_web,
        'is_monitoring': is_monitoring,
        # Envia a hora da última atividade para cálculo no frontend
        'last_desktop_update_iso': last_seen_desktop.isoformat() if last_seen_desktop else None
    }
    room = f'empresa_{empresa_id}'
    socketio.emit('agent_status_update', status_data, room=room)
    print(f"Broadcast Status para Agente {user_id} na sala {room}: Web={is_online_web}, Monitorando={is_monitoring}")

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        # Desconecta usuários não autenticados para segurança
        # disconnect() # Pode ser muito agressivo se houver reconexão
        print(f'Cliente não autenticado (SID: {request.sid}) tentou conectar.')
        return False # Rejeita a conexão

    user_id = current_user.id
    empresa_id = current_user.empresa_id
    sid = request.sid

    # Adiciona SID ao set do usuário
    if user_id not in online_users_web_sids:
        online_users_web_sids[user_id] = set()
    online_users_web_sids[user_id].add(sid)

    # Entra nas salas
    join_room(str(user_id)) # Sala pessoal
    if empresa_id:
        empresa_room = f'empresa_{empresa_id}'
        join_room(empresa_room) # Sala da empresa

    print(f'Cliente {current_user.nome} (ID: {user_id}, SID: {sid}) CONECTADO. Total SIDs: {len(online_users_web_sids[user_id])}. Status Web: True.')
    if empresa_id:
        broadcast_agent_status(user_id, empresa_id) # Notifica admins

@socketio.on('disconnect')
def handle_disconnect():
    # Usuário pode não estar mais autenticado aqui se a sessão expirou
    sid = request.sid
    user_id_found = None
    empresa_id_found = None

    # Encontra o usuário associado ao SID que desconectou
    for uid, sids in online_users_web_sids.items():
        if sid in sids:
            sids.remove(sid)
            user_id_found = uid
            # Tenta obter a empresa (pode falhar se o usuário foi deletado)
            from .models import Usuario # Import local
            user = Usuario.query.get(uid)
            if user:
                empresa_id_found = user.empresa_id
                print(f'Cliente {user.nome} (ID: {uid}, SID: {sid}) DESCONECTADO. SIDs restantes: {len(sids)}.')
            else:
                print(f'Cliente (ID: {uid}, SID: {sid}) DESCONECTADO (usuário não encontrado no DB). SIDs restantes: {len(sids)}.')

            # Se não há mais SIDs, o usuário está realmente offline da web
            if not sids:
                print(f'Usuário {uid} não tem mais conexões web ativas. Status Web: False.')
                # Remove a entrada para limpar memória (opcional)
                # del online_users_web_sids[uid]
            break # Sai do loop após encontrar e remover o SID

    if user_id_found and empresa_id_found:
        # Notifica os admins sobre a mudança de status web (pode ainda estar monitorando)
        broadcast_agent_status(user_id_found, empresa_id_found)
    elif not user_id_found:
        print(f'SID {sid} desconectado, mas não encontrado em online_users_web_sids.')


# Função chamada pela API quando recebe dados do desktop agent
def update_desktop_agent_status(agent_id, is_monitoring):
    """Atualiza o status de monitoramento vindo do desktop agent."""
    now = datetime.utcnow()
    # Garante que a entrada existe antes de atualizar
    if agent_id not in agent_desktop_status:
         agent_desktop_status[agent_id] = {}
    agent_desktop_status[agent_id]['monitoring'] = is_monitoring
    agent_desktop_status[agent_id]['last_seen'] = now
    print(f"Update Desktop Status para Agente {agent_id}: Monitorando={is_monitoring}, LastSeen={now.isoformat()}")

    # Encontra a empresa do agente para notificar a sala correta
    from .models import Usuario
    agent = Usuario.query.get(agent_id)
    if agent and agent.empresa_id:
        broadcast_agent_status(agent_id, agent.empresa_id)
    else:
        print(f"WARN: Não foi possível encontrar empresa para agente {agent_id} ao atualizar status desktop.")


# Tarefa de Verificação de Timeout (Idealmente rodaria em background com Celery/APScheduler)
def check_desktop_timeouts():
    """Verifica se algum agente desktop parou de enviar dados."""
    now = datetime.utcnow()
    timeout_threshold = timedelta(seconds=90) # Exemplo: 90 segundos
    agents_to_update = []

    for agent_id, status_info in agent_desktop_status.items():
        # Verifica apenas se estava monitorando e passou o tempo limite
        if status_info.get('monitoring') and status_info.get('last_seen'):
            if now - status_info['last_seen'] > timeout_threshold:
                agents_to_update.append(agent_id)

    if agents_to_update:
        print(f"TIMEOUT DETECTADO para agentes: {agents_to_update}")
        for agent_id in agents_to_update:
            update_desktop_agent_status(agent_id, False) # Marca como não monitorando

# Configura a verificação de timeout (Exemplo simples com timer, NÃO IDEAL para produção)
# Em produção, use APScheduler ou Celery beat.
import threading
def run_timeout_checker():
    # Roda a cada 60 segundos, por exemplo
    check_desktop_timeouts()
    threading.Timer(60.0, run_timeout_checker).start()

# Inicia o verificador de timeout (apenas se não estiver recarregando)
# Descomente a linha abaixo com cuidado em desenvolvimento, pode criar múltiplos timers.
# if not current_app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#      run_timeout_checker()