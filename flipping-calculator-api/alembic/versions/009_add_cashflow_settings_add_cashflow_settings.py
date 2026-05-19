"""add_cashflow_settings

Revision ID: 009_add_cashflow_settings
Revises: 008_baseline
Create Date: 2026-05-19 22:17:58.890375

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009_add_cashflow_settings'
down_revision: Union[str, Sequence[str], None] = '008_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (add cashflow settings columns)."""
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    
    if is_sqlite:
        # SQLite check
        res = bind.execute(sa.text("PRAGMA table_info(user_settings)"))
        columns = [row[1] for row in res.fetchall()]
    else:
        # Postgres check
        res = bind.execute(sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_settings'
        """))
        columns = [row[0] for row in res.fetchall()]
        
    if 'profit_take_pct' not in columns:
        op.add_column('user_settings', sa.Column('profit_take_pct', sa.Float(), server_default='0'))
    if 'loss_refill_pct' not in columns:
        op.add_column('user_settings', sa.Column('loss_refill_pct', sa.Float(), server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_settings', 'profit_take_pct')
    op.drop_column('user_settings', 'loss_refill_pct')
