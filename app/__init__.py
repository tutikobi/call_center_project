# call_center_project/app/__init__.py

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from .config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*") 

# Define o diretório de uploads no nível da aplicação
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__name__)), 'instance', 'uploads')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Garante que o diretório de uploads exista
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Inicializa o SocketIO com o app
    socketio.init_app(app)

    # Configurações do LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para aceder a esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        # Importa o modelo aqui para evitar importação circular
        from .models import Usuario
        return Usuario.query.get(int(user_id))
    
    # --- Registrar Blueprints ---
    
    # Autenticação
    from . import auth
    app.register_blueprint(auth.bp) # CORRIGIDO (era auth.auth)

    # Rotas do RH (a única versão correta)
    from .rh import routes as rh_routes
    app.register_blueprint(rh_routes.rh)
    
    # API
    from . import api
    app.register_blueprint(api.bp) # CORRIGIDO (era api.api)
    
    # Admin
    from . import admin
    app.register_blueprint(admin.bp) # CORRIGIDO (era admin.admin)
    
    # Management (Gestão de usuários, etc.)
    from . import management
    app.register_blueprint(management.bp)
    
    # Eventos de Socket.IO
    from . import socket_events

    # --- ROTA DE REDIRECIONAMENTO ---
    @app.route('/')
    def index():
        """Redireciona a rota raiz (/) para a página de login."""
        return redirect(url_for('auth.login'))
    # --- FIM DA ROTA ---
    
    return app
