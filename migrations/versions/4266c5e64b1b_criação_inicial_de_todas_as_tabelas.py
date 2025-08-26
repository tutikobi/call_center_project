"""Criação inicial de todas as tabelas

Revision ID: 4266c5e64b1b
Revises: 
Create Date: 2025-08-26 16:45:00.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4266c5e64b1b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Script de Criação Completo e Manual ###
    
    # 1. Tabela 'empresa' (sem dependências)
    op.create_table('empresa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('nome_empresa', sa.String(length=100), nullable=False),
        sa.Column('cnpj', sa.String(length=18), nullable=False),
        sa.Column('status_assinatura', sa.String(length=20), nullable=True),
        sa.Column('telefone_contato', sa.String(length=20), nullable=True),
        sa.Column('responsavel_contrato', sa.String(length=150), nullable=True),
        sa.Column('data_vencimento_pagamento', sa.DateTime(), nullable=True),
        sa.Column('forma_pagamento', sa.String(length=50), nullable=True),
        sa.Column('monitorar_reputacao', sa.Boolean(), nullable=True),
        sa.Column('google_reviews_url', sa.String(length=255), nullable=True),
        sa.Column('reclame_a_qui_url', sa.String(length=255), nullable=True),
        sa.Column('google_place_id', sa.String(length=255), nullable=True),
        sa.Column('whatsapp_token', sa.String(length=255), nullable=True),
        sa.Column('whatsapp_url', sa.String(length=255), nullable=True),
        sa.Column('webhook_verify_token', sa.String(length=255), nullable=True),
        sa.Column('status_pagamento', sa.String(length=20), nullable=False),
        sa.Column('duracao_contrato_meses', sa.Integer(), nullable=True),
        sa.Column('plano', sa.String(length=20), nullable=True),
        sa.Column('plano_email', sa.Boolean(), nullable=True),
        sa.Column('plano_whatsapp', sa.Boolean(), nullable=True),
        sa.Column('plano_rh', sa.Boolean(), nullable=True),
        sa.Column('plano_ia', sa.Boolean(), nullable=True),
        sa.Column('plano_api', sa.Boolean(), nullable=True),
        sa.Column('plano_relatorios_avancados', sa.Boolean(), nullable=True),
        sa.Column('plano_suporte_prioritario', sa.Boolean(), nullable=True),
        sa.Column('data_contrato', sa.DateTime(), nullable=True),
        sa.Column('valor_mensal', sa.Float(), nullable=True),
        sa.Column('max_usuarios', sa.Integer(), nullable=True),
        sa.Column('max_tickets_mes', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj')
    )

    # 2. Tabelas do RH que dependem de 'empresa'
    op.create_table('cargos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('salario_base', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('nivel', sa.String(length=20), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('departamentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('funcionarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('cpf', sa.String(length=14), nullable=False),
        sa.Column('rg', sa.String(length=20), nullable=False),
        sa.Column('data_nascimento', sa.Date(), nullable=False),
        sa.Column('sexo', sa.String(length=1), nullable=False),
        sa.Column('estado_civil', sa.String(length=20), nullable=False),
        sa.Column('telefone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('endereco', sa.Text(), nullable=False),
        sa.Column('cep', sa.String(length=9), nullable=False),
        sa.Column('cidade', sa.String(length=100), nullable=False),
        sa.Column('estado', sa.String(length=2), nullable=False),
        sa.Column('matricula', sa.String(length=20), nullable=False),
        sa.Column('cargo_id', sa.Integer(), nullable=False),
        sa.Column('departamento_id', sa.Integer(), nullable=False),
        sa.Column('salario', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('data_admissao', sa.Date(), nullable=False),
        sa.Column('data_demissao', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cargo_id'], ['cargos.id'], ),
        sa.ForeignKeyConstraint(['departamento_id'], ['departamentos.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cpf'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('matricula')
    )
    
    with op.batch_alter_table('departamentos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gestor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_departamentos_gestor_id_funcionarios', 'funcionarios', ['gestor_id'], ['id'])

    # 3. Tabela 'usuario' (depende de 'empresa' e 'departamentos')
    op.create_table('usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('whatsapp_numero', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('departamento_id', sa.Integer(), nullable=True),
        sa.Column('status_agente', sa.String(length=50), nullable=True),
        sa.Column('ultimo_login', sa.DateTime(), nullable=True),
        sa.Column('foto_perfil', sa.String(length=255), nullable=True),
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('cargo', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['departamento_id'], ['departamentos.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 4. Restantes tabelas da aplicação principal
    op.create_table('log_auditoria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('acao', sa.String(length=100), nullable=False),
        sa.Column('detalhes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('avaliacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('chamada_id', sa.String(length=100), nullable=True),
        sa.Column('canal', sa.String(length=20), nullable=True),
        sa.Column('csat', sa.Float(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('agente_id', sa.Integer(), nullable=False),
        sa.Column('nps', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['agente_id'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('conversa_whats_app',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('wa_id', sa.String(length=50), nullable=False),
        sa.Column('nome_cliente', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('inicio', sa.DateTime(), nullable=True),
        sa.Column('fim', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('agente_atribuido_id', sa.Integer(), nullable=True),
        sa.Column('assunto', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['agente_atribuido_id'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('email',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('agente_id', sa.Integer(), nullable=True),
        sa.Column('remetente', sa.String(length=150), nullable=False),
        sa.Column('assunto', sa.String(length=200), nullable=False),
        sa.Column('corpo', sa.Text(), nullable=True),
        sa.Column('data_recebimento', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['agente_id'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('mensagem_whats_app',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('conversa_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('remetente', sa.String(length=20), nullable=True),
        sa.Column('conteudo', sa.Text(), nullable=True),
        sa.Column('lida', sa.Boolean(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['conversa_id'], ['conversa_whats_app.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('notificacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('remetente_nome', sa.String(length=100), nullable=True),
        sa.Column('mensagem', sa.Text(), nullable=False),
        sa.Column('lida', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('reputacao_historico',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('data_registro', sa.DateTime(), nullable=False),
        sa.Column('nota_google', sa.Float(), nullable=True),
        sa.Column('total_avaliacoes_google', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('ticket_suporte',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('assunto', sa.String(length=200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('prioridade', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('anotacao_ticket',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('autor_id', sa.Integer(), nullable=False),
        sa.Column('conteudo', sa.Text(), nullable=False),
        sa.Column('is_solution', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['autor_id'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['ticket_id'], ['ticket_suporte.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('ticket_atividade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['ticket_suporte.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 5. Restantes tabelas do RH
    op.create_table('avaliacoes_desempenho',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('funcionario_id', sa.Integer(), nullable=False),
        sa.Column('avaliador_id', sa.Integer(), nullable=False),
        sa.Column('periodo_inicio', sa.Date(), nullable=False),
        sa.Column('periodo_fim', sa.Date(), nullable=False),
        sa.Column('produtividade', sa.Integer(), nullable=False),
        sa.Column('qualidade', sa.Integer(), nullable=False),
        sa.Column('pontualidade', sa.Integer(), nullable=False),
        sa.Column('relacionamento', sa.Integer(), nullable=False),
        sa.Column('iniciativa', sa.Integer(), nullable=False),
        sa.Column('nota_final', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('comentarios', sa.Text(), nullable=True),
        sa.Column('objetivos_proximos', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['avaliador_id'], ['funcionarios.id'], ),
        sa.ForeignKeyConstraint(['funcionario_id'], ['funcionarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ### end Alembic commands ###


def downgrade():
    # ### Comandos para reverter na ordem inversa ###
    op.drop_table('avaliacoes_desempenho')
    op.drop_table('ticket_atividade')
    op.drop_table('anotacao_ticket')
    op.drop_table('ticket_suporte')
    op.drop_table('reputacao_historico')
    op.drop_table('notificacao')
    op.drop_table('mensagem_whats_app')
    op.drop_table('email')
    op.drop_table('conversa_whats_app')
    op.drop_table('avaliacao')
    op.drop_table('log_auditoria')
    op.drop_table('usuario')
    with op.batch_alter_table('departamentos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_departamentos_gestor_id_funcionarios', type_='foreignkey')
    op.drop_table('funcionarios')
    op.drop_table('departamentos')
    op.drop_table('cargos')
    op.drop_table('empresa')
    # ### end Alembic commands ###