# call_center_project/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
import click
from flask_migrate import Migrate
from flask_socketio import SocketIO
from decimal import Decimal # Importar Decimal

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    # --- ALTERAÇÃO APLICADA AQUI: CRIAR E REGISTAR O FILTRO DE MOEDA ---
    def format_brl(value):
        """Filtro para formatar valores como moeda brasileira (R$)."""
        if value is None:
            return "R$ 0,00"
        try:
            # Converte para Decimal para garantir precisão
            val = Decimal(value)
            # Formata com 2 casas decimais, ponto como separador de milhar e vírgula para decimal
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters['brl'] = format_brl
    # --- FIM DA ALTERAÇÃO ---

    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    with app.app_context():
        from . import models, models_rh

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario
        return Usuario.query.get(int(user_id))

    @app.cli.command("init-db")
    def init_db_command():
        # ... (código do comando init-db) ...
        pass

    from . import routes, auth, api, admin, management, socket_events as events
    from .rh import routes as rh_routes

    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(management.bp)
    app.register_blueprint(rh_routes.rh)
    
    return app