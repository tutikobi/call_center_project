-- Script para criar as tabelas do módulo RH
-- Execute este SQL no seu banco de dados PostgreSQL

-- Tabela de Cargos
CREATE TABLE IF NOT EXISTS cargos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    salario_base DECIMAL(10, 2) NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Departamentos
CREATE TABLE IF NOT EXISTS departamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    gestor_id INTEGER, -- Será preenchido depois
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Funcionários
CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    rg VARCHAR(20) NOT NULL,
    data_nascimento DATE NOT NULL,
    sexo CHAR(1) NOT NULL CHECK (sexo IN ('M', 'F')),
    estado_civil VARCHAR(20) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    endereco TEXT NOT NULL,
    cep VARCHAR(9) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    cargo_id INTEGER NOT NULL REFERENCES cargos(id),
    departamento_id INTEGER NOT NULL REFERENCES departamentos(id),
    salario DECIMAL(10, 2) NOT NULL,
    data_admissao DATE NOT NULL,
    data_demissao DATE,
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'demitido', 'afastado')),
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adicionar a referência de gestor em Departamentos
ALTER TABLE departamentos ADD CONSTRAINT fk_gestor_id FOREIGN KEY (gestor_id) REFERENCES funcionarios(id);

-- Tabela de Controle de Ponto
CREATE TABLE IF NOT EXISTS controle_ponto (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    data DATE NOT NULL,
    entrada_1 TIME,
    saida_1 TIME,
    entrada_2 TIME,
    saida_2 TIME,
    horas_trabalhadas DECIMAL(4, 2) DEFAULT 0,
    horas_extras DECIMAL(4, 2) DEFAULT 0,
    observacoes TEXT,
    tipo_dia VARCHAR(20) DEFAULT 'normal' CHECK (tipo_dia IN ('normal', 'feriado', 'domingo')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(funcionario_id, data)
);

-- Tabela de Avaliações de Desempenho
CREATE TABLE IF NOT EXISTS avaliacoes_desempenho (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    avaliador_id INTEGER NOT NULL REFERENCES funcionarios(id),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    produtividade INTEGER NOT NULL CHECK (produtividade BETWEEN 1 AND 5),
    qualidade INTEGER NOT NULL CHECK (qualidade BETWEEN 1 AND 5),
    pontualidade INTEGER NOT NULL CHECK (pontualidade BETWEEN 1 AND 5),
    relacionamento INTEGER NOT NULL CHECK (relacionamento BETWEEN 1 AND 5),
    iniciativa INTEGER NOT NULL CHECK (iniciativa BETWEEN 1 AND 5),
    nota_final DECIMAL(3, 2) NOT NULL,
    comentarios TEXT,
    objetivos_proximos TEXT,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'finalizada')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Folha de Pagamento
CREATE TABLE IF NOT EXISTS folha_pagamento (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ano INTEGER NOT NULL,
    salario_base DECIMAL(10, 2) NOT NULL,
    horas_extras DECIMAL(10, 2) DEFAULT 0,
    adicional_noturno DECIMAL(10, 2) DEFAULT 0,
    comissoes DECIMAL(10, 2) DEFAULT 0,
    bonificacoes DECIMAL(10, 2) DEFAULT 0,
    inss DECIMAL(10, 2) DEFAULT 0,
    irrf DECIMAL(10, 2) DEFAULT 0,
    vale_transporte DECIMAL(10, 2) DEFAULT 0,
    vale_refeicao DECIMAL(10, 2) DEFAULT 0,
    plano_saude DECIMAL(10, 2) DEFAULT 0,
    outros_descontos DECIMAL(10, 2) DEFAULT 0,
    total_proventos DECIMAL(10, 2) DEFAULT 0,
    total_descontos DECIMAL(10, 2) DEFAULT 0,
    salario_liquido DECIMAL(10, 2) DEFAULT 0,
    dias_trabalhados INTEGER DEFAULT 0,
    faltas INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processando' CHECK (status IN ('processando', 'finalizada', 'paga')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(funcionario_id, mes, ano)
);