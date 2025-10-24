# Em run.py (ou seu arquivo principal)

from app import create_app, socketio
# [NOVO] Importe a função que inicia o monitoramento
from app.services.realtime_service import start_monitoring_thread

app = create_app()

if __name__ == '__main__':
    # [NOVO] Inicie o thread de monitoramento antes de rodar a app
    start_monitoring_thread()
    
    # Use o socketio.run() para rodar sua aplicação
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)