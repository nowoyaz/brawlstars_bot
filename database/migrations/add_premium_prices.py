"""Добавление таблицы premium_prices

Revision ID: add_premium_prices
Revises: add_filters_keywords
Create Date: 2024-04-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_premium_prices'
down_revision = 'add_filters_keywords'
branch_labels = None
depends_on = None

def upgrade():
    # Создаем таблицу premium_prices
    op.create_table(
        'premium_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False, unique=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Добавляем индекс
    op.create_index(op.f('ix_premium_prices_id'), 'premium_prices', ['id'], unique=False)
    op.create_index(op.f('ix_premium_prices_duration_days'), 'premium_prices', ['duration_days'], unique=True)
    
    # Добавляем данные по умолчанию
    op.bulk_insert(
        sa.table(
            'premium_prices',
            sa.column('duration_days', sa.Integer),
            sa.column('price', sa.Float)
        ),
        [
            {'duration_days': 30, 'price': 500.0},
            {'duration_days': 180, 'price': 2500.0},
            {'duration_days': 365, 'price': 4500.0},
            {'duration_days': 36500, 'price': 9900.0}
        ]
    )

def downgrade():
    # Удаляем таблицу при откате
    op.drop_index(op.f('ix_premium_prices_duration_days'), table_name='premium_prices')
    op.drop_index(op.f('ix_premium_prices_id'), table_name='premium_prices')
    op.drop_table('premium_prices') 