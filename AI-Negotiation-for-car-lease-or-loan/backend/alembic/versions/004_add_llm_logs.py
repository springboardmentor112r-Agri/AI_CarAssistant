"""Add llm_logs table

Revision ID: 004
Revises: 003
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

def upgrade():
  op.create_table(
    "llm_logs",
    sa.Column(
      "log_id",
      UUID(as_uuid=True),
      primary_key=True,
      server_default=sa.text("gen_random_uuid()")
    ),
    sa.Column(
      "timestamp",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False
    ),
    sa.Column("user_id", UUID(as_uuid=True), nullable=True),
    sa.Column("doc_id", UUID(as_uuid=True), nullable=True),
    sa.Column("thread_id", UUID(as_uuid=True), nullable=True),
    sa.Column(
      "module",
      sa.String(50),
      nullable=False
    ),
    # module values:
    #   "sla_extraction"
    #   "chat"
    #   "vin_pricing"
    sa.Column("model", sa.String(100), nullable=True),
    sa.Column("prompt_tokens", sa.Integer(), nullable=True),
    sa.Column("completion_tokens", sa.Integer(), nullable=True),
    sa.Column("total_tokens", sa.Integer(), nullable=True),
    sa.Column(
      "response_time_ms",
      sa.Integer(),
      nullable=True
    ),
    sa.Column(
      "success",
      sa.Boolean(),
      nullable=False,
      server_default="true"
    ),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column(
      "cost_estimate_usd",
      sa.Float(),
      nullable=True
    ),
    # Cost estimate based on Groq pricing
    # llama3-70b: $0.00059/1K input, $0.00079/1K output
  )

  # Indexes for fast dashboard queries
  op.create_index(
    "ix_llm_logs_timestamp",
    "llm_logs", ["timestamp"]
  )
  op.create_index(
    "ix_llm_logs_user_id",
    "llm_logs", ["user_id"]
  )
  op.create_index(
    "ix_llm_logs_module",
    "llm_logs", ["module"]
  )

def downgrade():
  op.drop_index("ix_llm_logs_module", "llm_logs")
  op.drop_index("ix_llm_logs_user_id", "llm_logs")
  op.drop_index("ix_llm_logs_timestamp", "llm_logs")
  op.drop_table("llm_logs")
