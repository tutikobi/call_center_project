# call_center_project/app/models.py

from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Classe base para adicionar campos de timestamp automaticamente
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Empresa(BaseModel):
    """Modelo Empresa com sistema de planos e chaves de API"""
    __tablename__ = 'empresa'
    nome_empresa = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    status_assinatura = db.Column(db.String(20), default='ativa')
    
    telefone_contato = db.Column(db.String(20), nullable=True)
    responsavel_contrato = db.Column(db.String(150), nullable=True)
    data_vencimento_pagamento = db.Column(db.DateTime, nullable=True)
    forma_pagamento = db.Column(db.String(50), default='boleto')
    monitorar_reputacao = db.Column(db.Boolean, default=False)
    google_reviews_url = db.Column(db.String(255), nullable=True)
    reclame_a_qui_url = db.Column(db.String(255), nullable=True)
    google_place_id = db.Column(db.String(255), nullable=True)
    status_pagamento = db.Column(db.String(20), nullable=False, default='em_dia')
    duracao_contrato_meses = db.Column(db.Integer, default=12)

    plano = db.Column(db.String(20), default='basico')
    plano_email = db.Column(db.Boolean, default=True)
    plano_whatsapp = db.Column(db.Boolean, default=True)
    plano_rh = db.Column(db.Boolean, default=False)
    plano_ia = db.Column(db.Boolean, default=False)
    plano_api = db.Column(db.Boolean, default=False)
    plano_relatorios_avancados = db.Column(db.Boolean, default=False)
    plano_suporte_prioritario = db.Column(db.Boolean, default=False)
    
    data_contrato = db.Column(db.DateTime, default=datetime.utcnow)
    valor_mensal = db.Column(db.Float, default=0.0)
    max_usuarios = db.Column(db.Integer, default=10)
    max_tickets_mes = db.Column(db.Integer, default=500)

    # --- CAMPOS DE API ATUALIZADOS E CENTRALIZADOS ---
    # WhatsApp Business API
    whatsapp_token = db.Column(db.String(255), nullable=True)
    whatsapp_phone_number_id = db.Column(db.String(255), nullable=True) # ID do número de telefone
    whatsapp_business_account_id = db.Column(db.String(255), nullable=True) # ID da conta do business
    webhook_verify_token = db.Column(db.String(255), nullable=True)
    
    # API de Email (Ex: SendGrid, Mailgun, etc.)
    email_api_key = db.Column(db.String(255), nullable=True)
    email_sender = db.Column(db.String(120), nullable=True) # Email remetente verificado no provedor

    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True, cascade="all, delete-orphan")
    avaliacoes = db.relationship('Avaliacao', backref='empresa', lazy=True, cascade="all, delete-orphan")
    conversas = db.relationship('ConversaWhatsApp', backref='empresa', lazy=True, cascade="all, delete-orphan")
    tickets_suporte = db.relationship('TicketSuporte', backref='empresa', lazy=True, cascade="all, delete-orphan")
    historico_reputacao = db.relationship('ReputacaoHistorico', backref='empresa', lazy=True, cascade="all, delete-orphan", order_by='ReputacaoHistorico.data_registro.desc()')
    emails = db.relationship('Email', backref='empresa', lazy=True, cascade="all, delete-orphan")
    logs_auditoria = db.relationship('LogAuditoria', backref='empresa', lazy=True)

    def get_recursos_habilitados(self):
        recursos = ['dashboard_basico', 'usuarios_basicos']
        if self.plano in ['medio', 'completo']:
             self.plano_rh = True
        
        if self.plano_email:
            recursos.extend(['email_management', 'email_monitoring'])
        if self.plano_whatsapp:
            recursos.extend(['whatsapp_integration', 'whatsapp_business'])
        if self.plano_rh:
            recursos.extend(['rh_module', 'folha_pagamento', 'rescisoes', 'adiantamentos'])
        if self.plano_ia:
            recursos.extend(['ai_classification', 'sentiment_analysis', 'ai_responses'])
        if self.plano_api:
            recursos.extend(['api_rest', 'api_webhooks', 'api_integrations'])
        if self.plano_relatorios_avancados:
            recursos.extend(['relatorios_avancados', 'analytics', 'dashboards_customizados'])
        if self.plano_suporte_prioritario:
            recursos.extend(['suporte_24h', 'suporte_dedicado'])
            
        return recursos
        
    def get_limite_usuarios(self):
        limites = {'basico': 5, 'medio': 15, 'completo': 50, 'customizado': self.max_usuarios}
        return limites.get(self.plano, 10)

class Usuario(UserMixin, BaseModel):
    __tablename__ = 'usuario'
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    whatsapp_numero = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='agente')
    status = db.Column(db.String(20), default='ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=True)
    status_agente = db.Column(db.String(50), default='Disponível')
    
    ultimo_login = db.Column(db.DateTime)
    foto_perfil = db.Column(db.String(255))
    telefone = db.Column(db.String(20))
    cargo = db.Column(db.String(50))
    
    avaliacoes = db.relationship('Avaliacao', backref='agente', lazy=True)
    conversas_atribuidas = db.relationship('ConversaWhatsApp', backref='agente_atribuido', lazy=True, foreign_keys='ConversaWhatsApp.agente_atribuido_id')
    emails = db.relationship('Email', backref='agente', lazy=True)
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade="all, delete-orphan")
    tickets_assigned = db.relationship('TicketSuporte', foreign_keys='TicketSuporte.assigned_to_id', backref='assignee', lazy=True)
    tickets_enviados = db.relationship('TicketSuporte', foreign_keys='TicketSuporte.usuario_id', backref='remetente', lazy=True)
    anotacoes_criadas = db.relationship('AnotacaoTicket', backref='autor', lazy=True)
    logs_auditoria = db.relationship('LogAuditoria', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.ultimo_login = datetime.utcnow()
        db.session.commit()

class LogAuditoria(BaseModel):
    __tablename__ = 'log_auditoria'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    acao = db.Column(db.String(100), nullable=False)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))

class Avaliacao(BaseModel):
    __tablename__ = 'avaliacao'
    chamada_id = db.Column(db.String(100))
    canal = db.Column(db.String(20))
    csat = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nps = db.Column(db.Integer)
    
class ConversaWhatsApp(BaseModel):
    __tablename__ = 'conversa_whats_app'
    wa_id = db.Column(db.String(50), nullable=False)
    nome_cliente = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ativo')
    inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fim = db.Column(db.DateTime)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    mensagens = db.relationship('MensagemWhatsApp', backref='conversa', lazy=True, cascade="all, delete-orphan", order_by='MensagemWhatsApp.timestamp')
    agente_atribuido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    assunto = db.Column(db.String(100), nullable=True, default='Geral')


class MensagemWhatsApp(BaseModel):
    __tablename__ = 'mensagem_whats_app'
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa_whats_app.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    remetente = db.Column(db.String(20))
    conteudo = db.Column(db.Text)
    lida = db.Column(db.Boolean, default=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)

class TicketSuporte(BaseModel):
    __tablename__ = 'ticket_suporte'
    assunto = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False, default='baixa')
    status = db.Column(db.String(20), nullable=False, default='aberto')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    anotacoes = db.relationship('AnotacaoTicket', backref='ticket', lazy=True, cascade="all, delete-orphan", order_by='AnotacaoTicket.created_at.asc()')
    atividades = db.relationship('TicketAtividade', backref='ticket', lazy=True, cascade="all, delete-orphan", order_by='TicketAtividade.timestamp.asc()')

class AnotacaoTicket(BaseModel):
    __tablename__ = 'anotacao_ticket'
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket_suporte.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    is_solution = db.Column(db.Boolean, default=False)

class TicketAtividade(BaseModel):
    __tablename__ = 'ticket_atividade'
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket_suporte.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    user = db.relationship('Usuario')
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ReputacaoHistorico(BaseModel):
    __tablename__ = 'reputacao_historico'
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    nota_google = db.Column(db.Float)
    total_avaliacoes_google = db.Column(db.Integer)

class Email(BaseModel):
    __tablename__ = 'email'
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    remetente = db.Column(db.String(150), nullable=False)
    assunto = db.Column(db.String(200), nullable=False)
    corpo = db.Column(db.Text)
    data_recebimento = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='nao_lido')

class Notificacao(BaseModel):
    __tablename__ = 'notificacao'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    remetente_nome = db.Column(db.String(100))
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False)