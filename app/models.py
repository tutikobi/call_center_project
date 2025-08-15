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
    whatsapp_token = db.Column(db.String(255))
    whatsapp_url = db.Column(db.String(255))
    webhook_verify_token = db.Column(db.String(255))
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True, cascade="all, delete-orphan")
    avaliacoes = db.relationship('Avaliacao', backref='empresa', lazy=True, cascade="all, delete-orphan")
    conversas = db.relationship('ConversaWhatsApp', backref='empresa', lazy=True, cascade="all, delete-orphan")
    # Novo relacionamento com tickets
    tickets_suporte = db.relationship('TicketSuporte', backref='empresa', lazy=True, cascade="all, delete-orphan")

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='agente')
    status = db.Column(db.String(20), nullable=False, default='ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    avaliacoes = db.relationship('Avaliacao', backref='agente', lazy=True)
    # Novo relacionamento com tickets
    tickets_enviados = db.relationship('TicketSuporte', backref='remetente', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

class MensagemWhatsApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa_whats_app.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    remetente = db.Column(db.String(20))
    conteudo = db.Column(db.Text)
    lida = db.Column(db.Boolean, default=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)

# --- NOVO MODELO ADICIONADO AQUI ---
class TicketSuporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assunto = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False, default='baixa') # baixa, media, alta
    status = db.Column(db.String(20), nullable=False, default='aberto') # aberto, em_andamento, fechado
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chaves estrangeiras para saber quem enviou
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
