# call_center_project/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
import click
from flask_migrate import Migrate # <-- ADICIONAR IMPORTAÇÃO

# Inicialização das extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate() # <-- ADICIONAR INICIALIZAÇÃO

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Inicializa as extensões com a aplicação
    db.init_app(app)
    migrate.init_app(app, db) # <-- ADICIONAR INICIALIZAÇÃO COM A APP
    login_manager.init_app(app)
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
        """Apaga as tabelas existentes e as recria do zero."""
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("Banco de dados inicializado: tabelas apagadas e recriadas.")

            if with_admin:
                create_super_admin_logic()

    def create_super_admin_logic():
        from .models import Empresa, Usuario

        nome_empresa_admin = "Sistema Call Center"
        email_admin = "admin@sistemacallcenter.com"

        empresa_admin = Empresa.query.filter_by(nome_empresa=nome_empresa_admin).first()
        if not empresa_admin:
            print(f"Criando empresa interna '{nome_empresa_admin}'...")
            empresa_admin = Empresa(
                nome_empresa=nome_empresa_admin,
                cnpj="00.000.000/0001-00",
                telefone_contato="(00) 0000-0000",
                status_assinatura="vitalicia"
            )
            db.session.add(empresa_admin)
            db.session.commit()
        else:
            print(f"Empresa interna '{nome_empresa_admin}' já existe.")

        if not Usuario.query.filter_by(email=email_admin).first():
            print(f"Criando super administrador com email '{email_admin}'...")
            admin = Usuario(
                nome="Super Admin",
                email=email_admin,
                role="super_admin",
                empresa_id=empresa_admin.id
            )
            admin.set_password("senhaSuperForte123")
            db.session.add(admin)
            db.session.commit()
            print("\n==========================================")
            print("Super administrador criado com sucesso!")
            print(f"Email: {email_admin}")
            print("Senha: senhaSuperForte123")
            print("==========================================")
        else:
            print("\nO usuário super administrador já existe no banco de dados.")

    from . import routes, auth, api, admin, management
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(management.bp)

    return app