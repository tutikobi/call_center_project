# call_center_project/run.py

from app import create_app, socketio
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # --- ALTERAÇÃO PARA PRODUÇÃO ---
    # O modo de desenvolvimento agora usa 'eventlet' como recomendado pelo SocketIO
    # para simular de forma mais próxima o ambiente de produção com Gunicorn.
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    
    # Para rodar localmente, você agora usará o comando: python run.py
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=True)

# --- COMANDO PARA USAR NO SERVIDOR DE PRODUÇÃO ---
#
# No seu servidor de produção (Heroku, Render, AWS), você não vai usar 'python run.py'.
# Em vez disso, você configurará o serviço para usar um comando Gunicorn parecido com este:
#
# gunicorn --worker-class eventlet -w 1 --log-level info "run:app"
#
# O que cada parte significa:
# -> gunicorn: Inicia o servidor Gunicorn.
# -> --worker-class eventlet: Informa ao Gunicorn para usar workers compatíveis com Socket.IO. Essencial!
# -> -w 1: (ou --workers 1) Comece com 1 worker. Você pode aumentar este número (ex: -w 4)
#           conforme a carga de usuários aumentar, para permitir mais acessos simultâneos.
# -> --log-level info: Define o nível de logs para exibir informações úteis.
# -> "run:app": Diz ao Gunicorn para procurar no arquivo 'run.py' a variável chamada 'app'.