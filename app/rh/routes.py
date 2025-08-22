# call_center_project/app/rh/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models_rh import Funcionario, Cargo, Departamento, AvaliacaoDesempenho, FolhaPagamento
from app.decorators import require_plan

rh = Blueprint('rh', __name__, url_prefix='/rh')

@rh.route('/dashboard')
@login_required
@require_plan('medio')
def dashboard():
    empresa_id = current_user.empresa_id
    total_funcionarios = Funcionario.query.filter_by(empresa_id=empresa_id, status='ativo').count()
    
    return render_template('rh/dashboard.html', total_funcionarios=total_funcionarios)

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
        try:
            ultimo = Funcionario.query.order_by(Funcionario.id.desc()).first()
            matricula = f"FUNC{str(ultimo.id + 1 if ultimo else 1).zfill(4)}"
            
            novo_func = Funcionario(
                nome=request.form['nome'],
                cpf=request.form['cpf'],
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
                salario=request.form['salario'],
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