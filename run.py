# call_center_project/run.py

from app import create_app, socketio
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)