"""Добавление поля premium_end_date

Revision ID: add_premium_end_date
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Добавляем колонку premium_end_date
    op.add_column('users', sa.Column('premium_end_date', sa.DateTime(), nullable=True))

def downgrade():
    # Удаляем колонку при откате
    op.drop_column('users', 'premium_end_date') 