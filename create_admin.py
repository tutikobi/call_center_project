# call_center_project/create_admin.py

from app import create_app, db
from app.models import Empresa, Usuario

app = create_app()

with app.app_context():
    print("Iniciando a criação do super administrador...")

    nome_empresa_admin = "Sistema Call Center"
    empresa_admin = Empresa.query.filter_by(nome_empresa=nome_empresa_admin).first()
    
    if not empresa_admin:
        print(f"Criando empresa interna '{nome_empresa_admin}'...")
        # --- CORREÇÃO APLICADA AQUI ---
        # Adicionamos um valor para o campo CNPJ, que é obrigatório.
        empresa_admin = Empresa(
            nome_empresa=nome_empresa_admin, 
            status_assinatura='vitalicia',
            cnpj='00.000.000/0000-00' # CNPJ genérico para a empresa do sistema
        )
        db.session.add(empresa_admin)
        db.session.commit()
        print("Empresa interna criada com sucesso.")
    else:
        print("Empresa interna já existe.")

    ADMIN_EMAIL = "admin@sistemacallcenter.com"
    ADMIN_PASSWORD = "senhaSuperForte123" 

    admin_user = Usuario.query.filter_by(email=ADMIN_EMAIL).first()

    if not admin_user:
        print(f"Criando usuário super administrador com o email: {ADMIN_EMAIL}")
        
        admin_user = Usuario(
            email=ADMIN_EMAIL,
            nome="Super Admin",
            role="super_admin",
            empresa_id=empresa_admin.id
        )
        
        admin_user.set_password(ADMIN_PASSWORD)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("\n=====================================================")
        print("  Super Administrador criado com sucesso!  ")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Senha: {ADMIN_PASSWORD}")
        print("=====================================================")
    else:
        print("\nO usuário super administrador já existe no banco de dados.")
