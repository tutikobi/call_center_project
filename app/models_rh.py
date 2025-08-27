# call_center_project/app/models_rh.py

from datetime import date, datetime
from app import db
from app.models import BaseModel

class Funcionario(BaseModel):
    __tablename__ = 'funcionarios'
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(1), nullable=False)
    estado_civil = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    cep = db.Column(db.String(9), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargos.id'), nullable=False)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=False)
    salario = db.Column(db.Numeric(10, 2), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    data_demissao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    foto_perfil = db.Column(db.String(255), nullable=True)
    
    jornada_trabalho = db.Column(db.String(20), default='5x2') 
    
    # --- CAMPOS DE VALOR (AGORA TODOS DIÁRIOS) ---
    vale_transporte_diario = db.Column(db.Numeric(10, 2), default=0.0)
    vale_alimentacao_diario = db.Column(db.Numeric(10, 2), default=0.0) # ATUALIZADO
    vale_refeicao_diario = db.Column(db.Numeric(10, 2), default=0.0)    # ATUALIZADO
    
    # --- CAMPOS DE CONTROLE (BOOLEAN) ---
    recebe_vt = db.Column(db.Boolean, default=False)
    recebe_va = db.Column(db.Boolean, default=False)
    recebe_vr = db.Column(db.Boolean, default=False)
    
    cargo = db.relationship('Cargo', backref='funcionarios')
    pontos = db.relationship('ControlePonto', backref='funcionario', lazy='dynamic')
    avaliacoes = db.relationship('AvaliacaoDesempenho', backref='funcionario', lazy='dynamic', foreign_keys='AvaliacaoDesempenho.funcionario_id')
    folhas = db.relationship('FolhaPagamento', backref='funcionario', lazy='dynamic')
    departamento = db.relationship('Departamento', foreign_keys=[departamento_id], back_populates='funcionarios')
    documentos = db.relationship('DocumentoFuncionario', backref='funcionario', lazy=True, cascade="all, delete-orphan")

# ... (o resto do arquivo permanece igual)
class Cargo(BaseModel):
    __tablename__ = 'cargos'
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    salario_base = db.Column(db.Numeric(10, 2), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    cbo = db.Column(db.String(10), nullable=True)

class Departamento(BaseModel):
    __tablename__ = 'departamentos'
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    gestor_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    funcionarios = db.relationship('Funcionario', foreign_keys='Funcionario.departamento_id', back_populates='departamento')
    gestor = db.relationship('Funcionario', foreign_keys=[gestor_id], post_update=True)

class DocumentoFuncionario(BaseModel):
    __tablename__ = 'documentos_funcionarios'
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(200), nullable=False)
    tipo_documento = db.Column(db.String(50), nullable=False)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)

class ControlePonto(BaseModel):
    __tablename__ = 'controle_ponto'
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    entrada_1 = db.Column(db.Time, nullable=True)
    saida_1 = db.Column(db.Time, nullable=True)
    entrada_2 = db.Column(db.Time, nullable=True)
    saida_2 = db.Column(db.Time, nullable=True)
    horas_trabalhadas = db.Column(db.Numeric(4, 2), default=0)
    horas_extras = db.Column(db.Numeric(4, 2), default=0)

class AvaliacaoDesempenho(BaseModel):
    __tablename__ = 'avaliacoes_desempenho'
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    avaliador_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fim = db.Column(db.Date, nullable=False)
    produtividade = db.Column(db.Integer, nullable=False)
    qualidade = db.Column(db.Integer, nullable=False)
    pontualidade = db.Column(db.Integer, nullable=False)
    relacionamento = db.Column(db.Integer, nullable=False)
    iniciativa = db.Column(db.Integer, nullable=False)
    nota_final = db.Column(db.Numeric(3, 2), nullable=False)
    comentarios = db.Column(db.Text)
    objetivos_proximos = db.Column(db.Text)
    status = db.Column(db.String(20), default='pendente')
    avaliador = db.relationship('Funcionario', foreign_keys=[avaliador_id])

class FolhaPagamento(BaseModel):
    __tablename__ = 'folha_pagamento'
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    salario_base = db.Column(db.Numeric(10, 2), nullable=False)
    horas_extras = db.Column(db.Numeric(10, 2), default=0)
    inss = db.Column(db.Numeric(10, 2), default=0)
    irrf = db.Column(db.Numeric(10, 2), default=0)
    vale_transporte = db.Column(db.Numeric(10, 2), default=0)
    vale_refeicao = db.Column(db.Numeric(10, 2), default=0)
    total_proventos = db.Column(db.Numeric(10, 2), default=0)
    total_descontos = db.Column(db.Numeric(10, 2), default=0)
    salario_liquido = db.Column(db.Numeric(10, 2), default=0)
    dias_trabalhados = db.Column(db.Integer, default=0)

class BeneficioFuncionario(BaseModel):
    __tablename__ = 'beneficios_funcionarios'
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    tipo_beneficio = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=True)