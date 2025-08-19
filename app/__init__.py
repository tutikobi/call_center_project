# call_center_project/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
import click
from flask_migrate import Migrate
from flask_socketio import SocketIO

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

    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario
        return Usuario.query.get(int(user_id))

    @app.cli.command("init-db")
    @click.option('--with-admin', is_flag=True, help='Cria o super administrador após inicializar o banco.')
    def init_db_command(with_admin):
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("Banco de dados inicializado.")
            if with_admin:
                create_super_admin_logic()

    def create_super_admin_logic():
        from .models import Empresa, Usuario
        nome_empresa_admin = "Sistema Call Center"
        empresa_admin = Empresa.query.filter_by(nome_empresa=nome_empresa_admin).first()
        if not empresa_admin:
            empresa_admin = Empresa(nome_empresa=nome_empresa_admin, cnpj="00.000.000/0001-00", status_assinatura="vitalicia")
            db.session.add(empresa_admin)
            db.session.commit()
        if not Usuario.query.filter_by(email="admin@sistemacallcenter.com").first():
            admin = Usuario(nome="Super Admin", email="admin@sistemacallcenter.com", role="super_admin", empresa_id=empresa_admin.id)
            admin.set_password("senhaSuperForte123")
            db.session.add(admin)
            db.session.commit()
            print("Super administrador criado com sucesso!")

    from . import routes, auth, api, admin, management, events
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(management.bp)
    
    return app