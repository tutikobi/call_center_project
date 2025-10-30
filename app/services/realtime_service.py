# call_center_project/app/services/realtime_service.py
from app import socketio
from app.models import db, Usuario
from datetime import datetime, timedelta
import time
import threading
from flask import current_app

# Define o tempo limite de inatividade em minutos
INACTIVITY_THRESHOLD_MINUTES = 3

def notify_dashboard_update(empresa_id: int, data: dict):
    """Envia uma notificação via WebSocket para a sala da empresa."""
    room_name = f'empresa_{empresa_id}'
    socketio.emit('productivity_update', data, room=room_name)

def check_inactive_agents():
    """
    Função que roda em loop para verificar agentes inativos.
    Esta função precisa ser executada dentro do contexto da aplicação Flask.
    """
    
    # --- [CORREÇÃO DO NameError APLICADA AQUI] ---
    # Importamos o create_app aqui dentro da função,
    # para evitar o erro de importação circular.
    from app import create_app
    app = create_app()  # Cria uma instância da app para ter o contexto
    # --- [FIM DA CORREÇÃO] ---
    
    with app.app_context():
        current_app.logger.info("Iniciando thread de verificação de agentes inativos...")
        while True:
            try:
                # Define o timestamp limite
                threshold = datetime.utcnow() - timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES)
                
                # Busca usuários que estão marcados como monitorando, 
                # mas cuja última atividade é mais antiga que o limite
                agentes_inativos = Usuario.query.filter(
                    Usuario.is_monitoring == True,
                    Usuario.last_agent_activity < threshold
                ).all()

                agentes_que_voltaram = Usuario.query.filter(
                    Usuario.is_monitoring == False,
                    Usuario.last_agent_activity >= threshold
                ).all()

                db_changed = False

                for agente in agentes_inativos:
                    agente.is_monitoring = False
                    agente.status_agente = 'Inativo' # Define o status principal como Inativo
                    db_changed = True
                    current_app.logger.info(f"Agente {agente.nome} (ID: {agente.id}) marcado como Inativo.")
                    # Emite um evento para o dashboard atualizar
                    socketio.emit('agent_status_update', {'user_id': agente.id, 'status': 'Inativo', 'is_monitoring': False}, room=f'empresa_{agente.empresa_id}')

                for agente in agentes_que_voltaram:
                    agente.is_monitoring = True
                    # Não mudamos o status_agente aqui, pois ele pode estar em "Pausa", etc.
                    # A rota /log_activity já define para "Disponível" se estava "Inativo"
                    db_changed = True
                    current_app.logger.info(f"Agente {agente.nome} (ID: {agente.id}) detectado como Ativo.")
                    socketio.emit('agent_status_update', {'user_id': agente.id, 'status': agente.status_agente, 'is_monitoring': True}, room=f'empresa_{agente.empresa_id}')


                if db_changed:
                    db.session.commit()
                
                # Emite um ping geral para todos os dashboards atualizarem
                # A rota /dashboard/produtividade será chamada pelos clientes
                if db_changed:
                    socketio.emit('atualizar_dashboard')

            except Exception as e:
                current_app.logger.error(f"Erro no thread de verificação de agentes: {e}")
                db.session.rollback() # Desfaz qualquer mudança em caso de erro
            
            # Espera 30 segundos antes de verificar novamente
            time.sleep(30)

def start_monitoring_thread():
    """
    Inicia o thread de monitoramento em segundo plano.
    """
    monitor_thread = threading.Thread(target=check_inactive_agents, daemon=True)
    monitor_thread.start()