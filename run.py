# call_center_project/run.py

from app import create_app, socketio
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Garante que o modo debug está ligado ao ambiente
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=True)