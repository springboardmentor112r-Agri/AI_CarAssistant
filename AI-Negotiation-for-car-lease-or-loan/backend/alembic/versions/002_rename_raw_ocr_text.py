"""Rename raw_ocr_text to raw_extracted_text

Revision ID: 002
Revises: 001
Create Date: 2024-01-01
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "documents",
        "raw_ocr_text",
        new_column_name="raw_extracted_text"
    )


def downgrade():
    op.alter_column(
        "documents",
        "raw_extracted_text",
        new_column_name="raw_ocr_text"
    )
