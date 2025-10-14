# call_center_project/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from decimal import Decimal
import os
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# --- CORREÇÃO APLICADA AQUI ---
# Removemos o 'async_mode' da inicialização global.
# O arquivo 'run.py' irá ativá-lo automaticamente ao executar.
socketio = SocketIO(message_queue=redis_url)

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_object(Config)
    app.config.from_prefixed_env() # Lê variáveis como OPENAI_API_KEY do .env

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        # Inicializa os novos serviços de produtividade
        from .services.ai_productivity_service import ai_productivity_service
        ai_productivity_service.init_app(app)
        # Nota: O realtime_service e redis_manager usam as instâncias globais e não precisam de init_app aqui.

    def format_brl(value):
        if value is None: return "R$ 0,00"
        try:
            return f"R$ {Decimal(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError): return value
    app.jinja_env.filters['brl'] = format_brl

    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    with app.app_context():
        # Garante que o Alembic (Flask-Migrate) reconheça todos os models
        from . import models, models_rh
        # Importa os novos models para que sejam "vistos" pela migração
        from app.models import ActivityLog, ProductivityRules

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario
        return Usuario.query.get(int(user_id))

    # Registra todos os Blueprints (rotas)
    from . import routes, auth, api, admin, management, socket_events
    from .rh import routes as rh_routes
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(management.bp)
    app.register_blueprint(rh_routes.rh)
    
    return app
