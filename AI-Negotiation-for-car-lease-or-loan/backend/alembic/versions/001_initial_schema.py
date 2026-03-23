"""001_initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-03-05 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # users
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # documents
    op.create_table(
        'documents',
        sa.Column('doc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('raw_ocr_text', sa.Text(), nullable=True),
        sa.Column('sla_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contract_fairness_score', sa.Float(), nullable=True),
        sa.Column('vin', sa.String(length=17), nullable=True),
        sa.Column('upload_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)

    # chat_history
    op.create_table(
        'chat_history',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.doc_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('message_id')
    )
    op.create_index(op.f('ix_chat_history_doc_id'), 'chat_history', ['doc_id'], unique=False)
    op.create_index(op.f('ix_chat_history_thread_id'), 'chat_history', ['thread_id'], unique=False)
    op.create_index(op.f('ix_chat_history_user_id'), 'chat_history', ['user_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_chat_history_user_id'), table_name='chat_history')
    op.drop_index(op.f('ix_chat_history_thread_id'), table_name='chat_history')
    op.drop_index(op.f('ix_chat_history_doc_id'), table_name='chat_history')
    op.drop_table('chat_history')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
