"""Add password_reset_tokens table

Revision ID: 005
Revises: 004
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

def upgrade():
  op.create_table(
    "password_reset_tokens",
    sa.Column(
      "id",
      UUID(as_uuid=True),
      primary_key=True,
      server_default=sa.text("gen_random_uuid()")
    ),
    sa.Column(
      "user_id",
      UUID(as_uuid=True),
      sa.ForeignKey("users.user_id", ondelete="CASCADE"),
      nullable=False,
    ),
    # Store SHA-256 hash of token, never plain token
    sa.Column(
      "token_hash",
      sa.String(64),
      nullable=False,
      unique=True,
    ),
    sa.Column(
      "expires_at",
      sa.DateTime(timezone=True),
      nullable=False,
    ),
    sa.Column(
      "used",
      sa.Boolean(),
      nullable=False,
      server_default="false",
    ),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
  )
  op.create_index(
    "ix_password_reset_tokens_user_id",
    "password_reset_tokens",
    ["user_id"]
  )
  op.create_index(
    "ix_password_reset_tokens_token_hash",
    "password_reset_tokens",
    ["token_hash"]
  )

def downgrade():
  op.drop_index(
    "ix_password_reset_tokens_token_hash",
    "password_reset_tokens"
  )
  op.drop_index(
    "ix_password_reset_tokens_user_id",
    "password_reset_tokens"
  )
  op.drop_table("password_reset_tokens")
