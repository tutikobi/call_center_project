# call_center_project/app/rh/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_from_directory, Response
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models_rh import Funcionario, Cargo, Departamento, DocumentoFuncionario
from app.decorators import require_plan
from .validators import is_cpf_valid
from .calculos import calcular_rescisao, calcular_folha_pagamento
import os
from werkzeug.utils import secure_filename
import openpyxl
from io import BytesIO
import json

rh = Blueprint('rh', __name__, url_prefix='/rh')

# --- FUNÇÃO AUXILIAR PARA UPLOADS ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'xlsx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROTAS PRINCIPAIS DO RH ---

@rh.route('/dashboard')
@login_required
@require_plan('medio')
def dashboard():
    empresa_id = current_user.empresa_id
    total_funcionarios = Funcionario.query.filter_by(empresa_id=empresa_id, status='ativo').count()
    total_departamentos = Departamento.query.filter_by(empresa_id=empresa_id).count()
    total_cargos = Cargo.query.filter_by(empresa_id=empresa_id).count()
    
    return render_template('rh/dashboard.html', 
        total_funcionarios=total_funcionarios,
        total_departamentos=total_departamentos,
        total_cargos=total_cargos)

# --- ROTAS PARA FUNCIONÁRIOS ---

@rh.route('/funcionarios')
@login_required
@require_plan('medio')
def listar_funcionarios():
    empresa_id = current_user.empresa_id
    funcionarios = Funcionario.query.filter_by(empresa_id=empresa_id).order_by(Funcionario.nome).all()
    return render_template('rh/funcionarios.html', funcionarios=funcionarios)

@rh.route('/funcionarios/novo', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def novo_funcionario():
    if request.method == 'POST':
        cpf = request.form['cpf']
        if not is_cpf_valid(cpf):
            flash('O CPF inserido é inválido. Por favor, verifique.', 'danger')
            cargos = Cargo.query.filter_by(empresa_id=current_user.empresa_id).all()
            departamentos = Departamento.query.filter_by(empresa_id=current_user.empresa_id).all()
            return render_template('rh/funcionario_form.html', cargos=cargos, departamentos=departamentos, form_data=request.form)

        try:
            ultimo = Funcionario.query.order_by(Funcionario.id.desc()).first()
            matricula = f"FUNC{str(ultimo.id + 1 if ultimo else 1).zfill(4)}"
            salario_str = request.form['salario'].replace('R$', '').replace('.', '').replace(',', '.').strip()

            novo_func = Funcionario(
                nome=request.form['nome'],
                cpf=cpf,
                rg=request.form['rg'],
                data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date(),
                sexo=request.form['sexo'],
                estado_civil=request.form['estado_civil'],
                telefone=request.form['telefone'],
                email=request.form['email'],
                endereco=request.form['endereco'],
                cep=request.form['cep'],
                cidade=request.form['cidade'],
                estado=request.form['estado'],
                matricula=matricula,
                cargo_id=request.form['cargo_id'],
                departamento_id=request.form['departamento_id'],
                salario=float(salario_str),
                data_admissao=datetime.strptime(request.form['data_admissao'], '%Y-%m-%d').date(),
                empresa_id=current_user.empresa_id
            )
            db.session.add(novo_func)
            db.session.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('rh.listar_funcionarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar funcionário: {str(e)}', 'danger')

    cargos = Cargo.query.filter_by(empresa_id=current_user.empresa_id).all()
    departamentos = Departamento.query.filter_by(empresa_id=current_user.empresa_id).all()
    
    return render_template('rh/funcionario_form.html', cargos=cargos, departamentos=departamentos)

@rh.route('/funcionarios/<int:id>')
@login_required
@require_plan('medio')
def ver_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_funcionarios'))

    documentos_pessoais = [doc for doc in funcionario.documentos if doc.tipo_documento != 'Atestado']
    atestados = [doc for doc in funcionario.documentos if doc.tipo_documento == 'Atestado']

    return render_template('rh/ver_funcionario.html', 
        funcionario=funcionario, 
        documentos_pessoais=documentos_pessoais,
        atestados=atestados)

@rh.route('/funcionarios/<int:id>/upload', methods=['POST'])
@login_required
@require_plan('medio')
def upload_documento(id):
    funcionario = Funcionario.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_funcionarios'))
    
    upload_type = request.form.get('upload_type')
    
    if upload_type not in ['foto', 'documento', 'atestado']:
        flash('Tipo de upload inválido.', 'danger')
        return redirect(url_for('rh.ver_funcionario', id=id))

    if 'file' not in request.files:
        flash('Nenhum ficheiro selecionado.', 'warning')
        return redirect(url_for('rh.ver_funcionario', id=id))

    file = request.files['file']
    if file.filename == '':
        flash('Nenhum ficheiro selecionado.', 'warning')
        return redirect(url_for('rh.ver_funcionario', id=id))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.instance_path, 'uploads', str(current_user.empresa_id), str(id))
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)

        if upload_type == 'foto':
            funcionario.foto_perfil = filename
            flash('Foto de perfil atualizada com sucesso!', 'success')
        else:
            tipo_doc = 'Atestado' if upload_type == 'atestado' else request.form.get('tipo_documento', 'Outro')
            novo_doc = DocumentoFuncionario(
                nome_arquivo=filename,
                tipo_documento=tipo_doc,
                caminho_arquivo=file_path,
                funcionario_id=id
            )
            db.session.add(novo_doc)
            flash(f'{tipo_doc} enviado com sucesso!', 'success')
        
        db.session.commit()
    else:
        flash('Tipo de ficheiro não permitido. Apenas: png, jpg, jpeg, pdf.', 'danger')

    return redirect(url_for('rh.ver_funcionario', id=id))

@rh.route('/uploads/<int:empresa_id>/<int:funcionario_id>/<filename>')
@login_required
def uploaded_file(empresa_id, funcionario_id, filename):
    if empresa_id != current_user.empresa_id:
        return "Acesso negado", 403
    path = os.path.join(current_app.instance_path, 'uploads', str(empresa_id), str(funcionario_id))
    return send_from_directory(path, filename)

@rh.route('/funcionarios/<int:id>/rescisao', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def calcular_rescisao_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_funcionarios'))

    resultado = None
    if request.method == 'POST':
        data_demissao = datetime.strptime(request.form['data_demissao'], '%Y-%m-%d').date()
        motivo = request.form['motivo']
        aviso_indenizado = 'aviso_indenizado' in request.form
        ferias_vencidas = 'ferias_vencidas' in request.form
        
        resultado = calcular_rescisao(
            salario_bruto=funcionario.salario,
            data_admissao=funcionario.data_admissao,
            data_demissao=data_demissao,
            motivo=motivo,
            aviso_previo_indenizado=aviso_indenizado,
            ferias_vencidas=ferias_vencidas
        )

    return render_template('rh/rescisao_form.html', funcionario=funcionario, resultado=resultado)

@rh.route('/funcionarios/<int:id>/folha_pagamento', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def simular_folha_pagamento(id):
    funcionario = Funcionario.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_funcionarios'))

    resultado = None
    if request.method == 'POST':
        dias_uteis = int(request.form.get('dias_uteis', 22))
        valor_diario_vt = float(request.form.get('valor_diario_vt', 0).replace(',', '.'))
        valor_mensal_va = float(request.form.get('valor_mensal_va', 0).replace(',', '.'))

        resultado = calcular_folha_pagamento(
            salario_bruto=funcionario.salario,
            dias_uteis=dias_uteis,
            valor_diario_vt=valor_diario_vt,
            valor_mensal_va=valor_mensal_va
        )

    return render_template('rh/folha_pagamento_form.html', funcionario=funcionario, resultado=resultado)

@rh.route('/funcionarios/importar', methods=['POST'])
@login_required
@require_plan('medio')
def importar_funcionarios():
    if 'excel_file' not in request.files:
        flash('Nenhum ficheiro selecionado.', 'warning')
        return redirect(url_for('rh.listar_funcionarios'))

    file = request.files['excel_file']

    if file.filename == '' or not allowed_file(file.filename):
        flash('Ficheiro inválido ou não selecionado. Por favor, use um ficheiro .xlsx.', 'danger')
        return redirect(url_for('rh.listar_funcionarios'))

    try:
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        header = [cell.value for cell in sheet[1]]
        
        sucesso = 0
        erros = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            data = dict(zip(header, row))
            
            if not all([data.get('nome'), data.get('cpf'), data.get('email'), data.get('cargo'), data.get('departamento')]):
                erros += 1
                continue
            
            if not is_cpf_valid(data['cpf']):
                erros += 1
                continue

            cargo = Cargo.query.filter_by(nome=data['cargo'], empresa_id=current_user.empresa_id).first()
            departamento = Departamento.query.filter_by(nome=data['departamento'], empresa_id=current_user.empresa_id).first()

            if not cargo or not departamento:
                erros += 1
                continue
            
            try:
                data_nasc = datetime.strptime(data['data_nascimento'], '%d/%m/%Y').date()
                data_adm = datetime.strptime(data['data_admissao'], '%d/%m/%Y').date()
            except (ValueError, TypeError):
                erros += 1
                continue

            novo_func = Funcionario(
                nome=data['nome'],
                cpf=data['cpf'],
                rg=data.get('rg', ''),
                data_nascimento=data_nasc,
                sexo=data.get('sexo', 'M'),
                estado_civil=data.get('estado_civil', 'Solteiro(a)'),
                telefone=data.get('telefone', ''),
                email=data['email'],
                endereco=data.get('endereco', ''),
                cep=data.get('cep', ''),
                cidade=data.get('cidade', ''),
                estado=data.get('estado', ''),
                salario=float(data.get('salario', 0)),
                data_admissao=data_adm,
                cargo_id=cargo.id,
                departamento_id=departamento.id,
                empresa_id=current_user.empresa_id
            )
            ultimo = Funcionario.query.order_by(Funcionario.id.desc()).first()
            novo_func.matricula = f"FUNC{str(ultimo.id + 1 if ultimo else 1).zfill(4)}"
            
            db.session.add(novo_func)
            sucesso += 1

        db.session.commit()
        flash(f'Importação concluída! {sucesso} funcionários importados com sucesso. {erros} linhas continham erros e foram ignoradas.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao processar o ficheiro: {e}', 'danger')

    return redirect(url_for('rh.listar_funcionarios'))

@rh.route('/funcionarios/template')
@login_required
def download_template():
    output = BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Modelo de Importação"

    headers = [
        "nome", "cpf", "email", "data_nascimento", "data_admissao", "salario",
        "cargo", "departamento", "rg", "sexo", "estado_civil", "telefone",
        "endereco", "cep", "cidade", "estado"
    ]
    sheet.append(headers)

    example = [
        "João da Silva", "123.456.789-00", "joao.silva@exemplo.com", "15/05/1990", "01/08/2025",
        "3500.50", "Analista Financeiro", "Financeiro", "1234567", "M", "Casado(a)",
        "(51) 99999-8888", "Rua das Flores, 123", "90000-000", "Porto Alegre", "RS"
    ]
    sheet.append(example)
    
    workbook.save(output)
    output.seek(0)
    
    return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment;filename=template_funcionarios.xlsx"})


# --- ROTAS PARA DEPARTAMENTOS ---

@rh.route('/departamentos')
@login_required
@require_plan('medio')
def listar_departamentos():
    departamentos = Departamento.query.filter_by(empresa_id=current_user.empresa_id).order_by(Departamento.nome).all()
    return render_template('rh/departamentos.html', departamentos=departamentos)

@rh.route('/departamentos/novo', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def novo_departamento():
    if request.method == 'POST':
        novo_depto = Departamento(
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            empresa_id=current_user.empresa_id
        )
        db.session.add(novo_depto)
        db.session.commit()
        flash('Departamento criado com sucesso!', 'success')
        return redirect(url_for('rh.listar_departamentos'))
    return render_template('rh/departamento_form.html', title="Novo Departamento")

@rh.route('/departamentos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def editar_departamento(id):
    depto = Departamento.query.get_or_404(id)
    if depto.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_departamentos'))
    
    if request.method == 'POST':
        depto.nome = request.form['nome']
        depto.descricao = request.form['descricao']
        db.session.commit()
        flash('Departamento atualizado com sucesso!', 'success')
        return redirect(url_for('rh.listar_departamentos'))
    return render_template('rh/departamento_form.html', title="Editar Departamento", departamento=depto)

# --- ROTAS PARA CARGOS ---

@rh.route('/cargos')
@login_required
@require_plan('medio')
def listar_cargos():
    cargos = Cargo.query.filter_by(empresa_id=current_user.empresa_id).order_by(Cargo.nome).all()
    return render_template('rh/cargos.html', cargos=cargos)

@rh.route('/cargos/novo', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def novo_cargo():
    if request.method == 'POST':
        salario_str = request.form['salario_base'].replace('R$', '').replace('.', '').replace(',', '.').strip()
        novo_cargo = Cargo(
            nome=request.form['nome'],
            cbo=request.form['cbo'],
            descricao=request.form['descricao'],
            salario_base=float(salario_str),
            nivel=request.form['nivel'],
            empresa_id=current_user.empresa_id
        )
        db.session.add(novo_cargo)
        db.session.commit()
        flash('Cargo criado com sucesso!', 'success')
        return redirect(url_for('rh.listar_cargos'))
    
    cbo_data = {}
    try:
        cbo_file_path = os.path.join(current_app.static_folder, 'data', 'cbo.json')
        with open(cbo_file_path, 'r', encoding='utf-8') as f:
            cbo_data = json.load(f)
    except Exception as e:
        flash(f"Atenção: Não foi possível carregar a lista de CBOs. A busca automática está desativada. Erro: {e}", "warning")

    return render_template('rh/cargo_form.html', title="Novo Cargo", cbo_data=cbo_data)

@rh.route('/cargos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_plan('medio')
def editar_cargo(id):
    cargo = Cargo.query.get_or_404(id)
    if cargo.empresa_id != current_user.empresa_id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.listar_cargos'))

    if request.method == 'POST':
        salario_str = request.form['salario_base'].replace('R$', '').replace('.', '').replace(',', '.').strip()
        cargo.nome = request.form['nome']
        cargo.cbo = request.form['cbo']
        cargo.descricao = request.form['descricao']
        cargo.salario_base = float(salario_str)
        cargo.nivel = request.form['nivel']
        db.session.commit()
        flash('Cargo atualizado com sucesso!', 'success')
        return redirect(url_for('rh.listar_cargos'))
    
    cbo_data = {}
    try:
        cbo_file_path = os.path.join(current_app.static_folder, 'data', 'cbo.json')
        with open(cbo_file_path, 'r', encoding='utf-8') as f:
            cbo_data = json.load(f)
    except Exception as e:
        flash(f"Atenção: Não foi possível carregar a lista de CBOs. A busca automática está desativada. Erro: {e}", "warning")

    return render_template('rh/cargo_form.html', title="Editar Cargo", cargo=cargo, cbo_data=cbo_data)