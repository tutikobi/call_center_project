# call_center_project/app/management.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, Usuario, Empresa, TicketSuporte
# --- ALTERAÇÃO 1: IMPORTAR O MODELO DE DEPARTAMENTO ---
from .models_rh import Departamento
from flask_login import login_required, current_user
from functools import wraps
from .ai_service import load_knowledge_base, get_ai_response

bp = Blueprint('management', __name__, url_prefix='/management' )

knowledge_base = load_knowledge_base()

PLAN_LIMITS = {
    'basico': 5,
    'medio': 10,
    'pro': 20
}

def empresa_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin_empresa':
            flash("Você não tem permissão para acessar esta área.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/usuarios')
@login_required
@empresa_admin_required
def listar_usuarios():
    usuarios_da_empresa = Usuario.query.filter_by(empresa_id=current_user.empresa_id).order_by(Usuario.nome).all()
    return render_template('management/listar_usuarios.html', usuarios=usuarios_da_empresa, page_title="Gerenciar Usuários")

@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def novo_usuario():
    empresa_atual = current_user.empresa
    plano_da_empresa = empresa_atual.plano
    limite_agentes = PLAN_LIMITS.get(plano_da_empresa, 0)
    total_usuarios = Usuario.query.filter(Usuario.empresa_id == current_user.empresa_id, Usuario.role.in_(['agente', 'admin_empresa'])).count()

    if total_usuarios >= limite_agentes:
        flash(f'O limite de {limite_agentes} usuários para o plano "{plano_da_empresa.capitalize()}" foi atingido.', 'danger')
        return redirect(url_for('management.listar_usuarios'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        whatsapp = request.form.get('whatsapp_numero')
        senha = request.form.get('senha')
        role = request.form.get('role', 'agente')
        # --- ALTERAÇÃO 2: OBTER O DEPARTAMENTO DO FORMULÁRIO ---
        departamento_id = request.form.get('departamento_id')
        
        if not all([nome, email, senha, whatsapp]):
            flash('Todos os campos são obrigatórios.', 'warning')
            return render_template('management/form_usuario.html', page_title="Novo Usuário", form_data=request.form)
            
        if Usuario.query.filter_by(email=email).first():
            flash(f'O email "{email}" já está em uso.', 'danger')
            return render_template('management/form_usuario.html', page_title="Novo Usuário", form_data=request.form)
        
        # --- ALTERAÇÃO 3: ADICIONAR O DEPARTAMENTO AO NOVO USUÁRIO ---
        novo_usuario = Usuario(
            nome=nome, 
            email=email, 
            whatsapp_numero=whatsapp, 
            role=role, 
            empresa_id=current_user.empresa_id,
            departamento_id=int(departamento_id) if departamento_id else None
        )
        novo_usuario.set_password(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        flash(f'Usuário "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('management.listar_usuarios'))
    
    # --- ALTERAÇÃO 4: BUSCAR DEPARTAMENTOS PARA ENVIAR AO TEMPLATE ---
    departamentos = Departamento.query.filter_by(empresa_id=current_user.empresa_id).order_by(Departamento.nome).all()
    return render_template('management/form_usuario.html', page_title="Novo Usuário", departamentos=departamentos)

@bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))

    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.role = request.form.get('role')
        # --- ALTERAÇÃO 5: ATUALIZAR O DEPARTAMENTO ---
        departamento_id = request.form.get('departamento_id')
        usuario.departamento_id = int(departamento_id) if departamento_id else None

        if current_user.role != 'super_admin':
            if usuario.email != request.form.get('email') or usuario.whatsapp_numero != request.form.get('whatsapp_numero'):
                flash("Email e WhatsApp não podem ser alterados. Por favor, abra um ticket de suporte.", "warning")
                return redirect(url_for('management.editar_usuario', id=id))
        
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.set_password(nova_senha)
            flash('Senha atualizada com sucesso.', 'info')

        db.session.commit()
        flash(f'Dados do usuário "{usuario.nome}" atualizados com sucesso!', 'success')
        return redirect(url_for('management.listar_usuarios'))
    
    # --- ALTERAÇÃO 6: BUSCAR DEPARTAMENTOS PARA ENVIAR AO TEMPLATE ---
    departamentos = Departamento.query.filter_by(empresa_id=current_user.empresa_id).order_by(Departamento.nome).all()
    return render_template('management/form_usuario.html', page_title=f"Editar Usuário: {usuario.nome}", usuario=usuario, is_edit=True, departamentos=departamentos)

@bp.route('/usuarios/<int:id>/toggle_status', methods=['POST'])
@login_required
@empresa_admin_required
def toggle_status_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.id == current_user.id:
        flash("Você não pode bloquear seu próprio acesso.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.status == 'ativo':
        usuario.status = 'bloqueado'
        flash(f'O acesso do usuário "{usuario.nome}" foi bloqueado.', 'warning')
    else:
        usuario.status = 'ativo'
        flash(f'O acesso do usuário "{usuario.nome}" foi reativado.', 'success')
    db.session.commit()
    return redirect(url_for('management.listar_usuarios'))

@bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_required
@empresa_admin_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.empresa_id != current_user.empresa_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('management.listar_usuarios'))
    if usuario.id == current_user.id:
        flash("Você não pode excluir seu próprio usuário.", 'danger')
        return redirect(url_for('management.listar_usuarios'))
    db.session.delete(usuario)
    db.session.commit()
    flash(f'O usuário "{usuario.nome}" foi excluído permanentemente.', 'danger')
    return redirect(url_for('management.listar_usuarios'))

@bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@empresa_admin_required
def configuracoes():
    empresa = Empresa.query.get(current_user.empresa_id)
    if request.method == 'POST':
        empresa.whatsapp_token = request.form.get('whatsapp_token')
        empresa.whatsapp_url = request.form.get('whatsapp_url')
        empresa.webhook_verify_token = request.form.get('webhook_verify_token')
        db.session.commit()
        flash('Configurações de API salvas com sucesso!', 'success')
        return redirect(url_for('management.configuracoes'))
    return render_template('management/configuracoes.html', empresa=empresa, page_title="Configurações da API")

@bp.route('/suporte/sugestao_ia', methods=['POST'])
@login_required
def sugestao_ia():
    descricao = request.json.get('descricao', '')
    if len(descricao) < 10:
        return jsonify({
            'status': 'not_found', 
            'sugestao': 'Por favor, forneça mais detalhes sobre seu problema para que eu possa te ajudar melhor.'
        })

    resposta = get_ai_response(descricao, knowledge_base)

    if resposta:
        return jsonify({'status': 'found', 'sugestao': resposta})
    else:
        return jsonify({
            'status': 'not_found', 
            'sugestao': 'Não encontrei uma solução na minha base de conhecimento. Para garantir que seu problema seja resolvido, estou abrindo um ticket para nossa equipe de suporte.'
        })

@bp.route('/suporte/auto_create_ticket', methods=['POST'])
@login_required
def auto_create_ticket():
    data = request.json
    topic = data.get('topic')
    description = data.get('description')

    if not all([topic, description]):
        return jsonify({'status': 'error', 'message': 'Faltam dados para criar o ticket.'}), 400

    if topic == "Suporte Técnico" or "parado" in description.lower() or "erro" in description.lower():
        prioridade = "alta"
    elif topic == "Problemas com Fatura":
        prioridade = "media"
    else:
        prioridade = "baixa"

    novo_ticket = TicketSuporte(
        assunto=f"Ticket Automático: {topic}",
        descricao=description,
        prioridade=prioridade,
        status='aberto',
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id
    )
    db.session.add(novo_ticket)
    db.session.commit()

    return jsonify({'status': 'ok', 'message': 'Ticket criado com sucesso!'})

@bp.route('/suporte/novo_ticket', methods=['POST'])
@login_required
def novo_ticket():
    if current_user.role == 'super_admin':
        flash("O super admin não pode abrir tickets.", "danger")
        return redirect(request.referrer or url_for('routes.dashboard'))
    assunto = request.form.get('assunto')
    descricao = request.form.get('descricao')
    if not all([assunto, descricao]):
        flash("Todos os campos do ticket são obrigatórios.", "warning")
        return redirect(request.referrer or url_for('routes.dashboard'))
    if assunto in ["Suporte Técnico", "Problema em Relatórios"]:
        prioridade = "alta"
    elif assunto == "Emissão de Fatura":
        prioridade = "media"
    else:
        prioridade = "baixa"
    novo_ticket = TicketSuporte(
        assunto=assunto,
        descricao=descricao,
        prioridade=prioridade,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id
    )
    db.session.add(novo_ticket)
    db.session.commit()
    flash("Seu ticket de suporte foi enviado com sucesso! Entraremos em contato em breve.", "success")
    return redirect(request.referrer or url_for('routes.dashboard'))