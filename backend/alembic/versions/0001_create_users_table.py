# backend/alembic/versions/0001_create_users_table.py
"""create users table

Revision ID: 0001
Revises: 
Create Date: 2025-10-09

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("mobile_number", sa.String(), nullable=False),
        sa.Column("language_pref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    # Index + unique constraint equivalent to model
    op.create_index("ix_users_mobile_number", "users", ["mobile_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_mobile_number", table_name="users")
    op.drop_table("users")
