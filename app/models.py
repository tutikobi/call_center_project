# call_center_project/app/models.py

from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    telefone_contato = db.Column(db.String(20))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    status_assinatura = db.Column(db.String(20), default='ativa')
    status_pagamento = db.Column(db.String(20), nullable=False, default='em_dia')
    plano = db.Column(db.String(50), nullable=False, default='basico')
    responsavel_contrato = db.Column(db.String(150))
    data_contrato = db.Column(db.DateTime, default=datetime.utcnow)
    duracao_contrato_meses = db.Column(db.Integer, default=12)
    data_vencimento_pagamento = db.Column(db.DateTime)
    forma_pagamento = db.Column(db.String(50), default='boleto')
    monitorar_reputacao = db.Column(db.Boolean, default=False)
    google_reviews_url = db.Column(db.String(255))
    reclame_aqui_url = db.Column(db.String(255))
    google_place_id = db.Column(db.String(255))
    whatsapp_token = db.Column(db.String(255))
    whatsapp_url = db.Column(db.String(255))
    webhook_verify_token = db.Column(db.String(255))
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True, cascade="all, delete-orphan")
    avaliacoes = db.relationship('Avaliacao', backref='empresa', lazy=True, cascade="all, delete-orphan")
    conversas = db.relationship('ConversaWhatsApp', backref='empresa', lazy=True, cascade="all, delete-orphan")
    tickets_suporte = db.relationship('TicketSuporte', backref='empresa', lazy=True, cascade="all, delete-orphan")
    historico_reputacao = db.relationship('ReputacaoHistorico', backref='empresa', lazy=True, cascade="all, delete-orphan", order_by='ReputacaoHistorico.data_registro.desc()')
    emails = db.relationship('Email', backref='empresa', lazy=True, cascade="all, delete-orphan")

class ReputacaoHistorico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    nota_google = db.Column(db.Float)
    total_avaliacoes_google = db.Column(db.Integer)
    nota_reclame_aqui = db.Column(db.Float)
    total_reclamacoes_reclame_aqui = db.Column(db.Integer)
    observacoes = db.Column(db.Text)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    whatsapp_numero = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='agente')
    status = db.Column(db.String(20), nullable=False, default='ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    avaliacoes = db.relationship('Avaliacao', backref='agente', lazy=True)
    tickets_enviados = db.relationship('TicketSuporte', backref='remetente', lazy=True)
    anotacoes_criadas = db.relationship('AnotacaoTicket', backref='autor', lazy=True)
    emails = db.relationship('Email', backref='agente', lazy=True)
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    remetente = db.Column(db.String(150), nullable=False)
    assunto = db.Column(db.String(200), nullable=False)
    corpo = db.Column(db.Text)
    data_recebimento = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='nao_lido')

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    remetente_nome = db.Column(db.String(100))
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    chamada_id = db.Column(db.String(100))
    canal = db.Column(db.String(20))
    csat = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class ConversaWhatsApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wa_id = db.Column(db.String(50), nullable=False)
    nome_cliente = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ativo')
    inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fim = db.Column(db.DateTime)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    mensagens = db.relationship('MensagemWhatsApp', backref='conversa', lazy=True, cascade="all, delete-orphan", order_by='MensagemWhatsApp.timestamp')
    agente_atribuido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    agente_atribuido = db.relationship('Usuario', foreign_keys=[agente_atribuido_id])

class MensagemWhatsApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa_whats_app.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    remetente = db.Column(db.String(20))
    conteudo = db.Column(db.Text)
    lida = db.Column(db.Boolean, default=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)

class TicketSuporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assunto = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False, default='baixa')
    status = db.Column(db.String(20), nullable=False, default='aberto')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    anotacoes = db.relationship('AnotacaoTicket', backref='ticket', lazy=True, cascade="all, delete-orphan", order_by='AnotacaoTicket.data_criacao.asc()')

class AnotacaoTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket_suporte.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)