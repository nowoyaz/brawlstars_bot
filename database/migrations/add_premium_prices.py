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
        sa.Column('duration_type', sa.String(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Добавляем индекс
    op.create_index(op.f('ix_premium_prices_id'), 'premium_prices', ['id'], unique=False)
    
    # Добавляем данные по умолчанию
    op.bulk_insert(
        sa.table(
            'premium_prices',
            sa.column('duration_type', sa.String),
            sa.column('price', sa.Integer)
        ),
        [
            {'duration_type': 'month', 'price': 500},
            {'duration_type': 'half_year', 'price': 2500},
            {'duration_type': 'year', 'price': 4500},
            {'duration_type': 'forever', 'price': 9900}
        ]
    )

def downgrade():
    # Удаляем таблицу при откате
    op.drop_index(op.f('ix_premium_prices_id'), table_name='premium_prices')
    op.drop_table('premium_prices') 