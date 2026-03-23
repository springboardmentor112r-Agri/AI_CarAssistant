"""Update processing status values

Revision ID: 003
Revises: 002
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

def upgrade():
  # Rename ocr_complete to extraction_complete in existing rows
  op.execute(
    """
    UPDATE documents
    SET processing_status = 'extraction_complete'
    WHERE processing_status = 'ocr_complete'
    """
  )
  # Add sla_retry_count column to track retry attempts
  op.add_column(
    "documents",
    sa.Column(
      "sla_retry_count",
      sa.Integer(),
      nullable=False,
      server_default="0"
    )
  )

def downgrade():
  op.execute(
    """
    UPDATE documents
    SET processing_status = 'ocr_complete'
    WHERE processing_status = 'extraction_complete'
    """
  )
  op.drop_column("documents", "sla_retry_count")
