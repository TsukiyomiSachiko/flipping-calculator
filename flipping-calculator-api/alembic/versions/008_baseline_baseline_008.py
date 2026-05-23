"""baseline_008

Revision ID: 008_baseline
Revises: 
Create Date: 2026-05-19 22:17:45.026849

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_baseline'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (baseline up to migration 008)."""
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    # 1. Accounts table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS accounts (
            id {pk_type},
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            password_hash TEXT
        )
    """)
    
    # 2. Items table (id is the OSRS item ID, not auto-increment)
    op.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            examine TEXT,
            members BOOLEAN,
            lowalch INTEGER,
            highalch INTEGER,
            value INTEGER,
            ge_limit INTEGER,
            icon TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Index on item name
    op.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
    
    # 3. User flips table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS user_flips (
            id {pk_type},
            account_id INTEGER,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity_total INTEGER NOT NULL,
            quantity_remaining INTEGER NOT NULL,
            buy_price INTEGER NOT NULL,
            sell_price INTEGER,
            intended_sell_price INTEGER,
            buy_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sell_time TIMESTAMP,
            profit INTEGER,
            roi REAL,
            status TEXT DEFAULT 'pending',
            cancel_reason TEXT,
            notes TEXT,
            intended_quantity INTEGER,
            buy_offer_started_at TIMESTAMP,
            last_buy_at TIMESTAMP,
            sell_offer_started_at TIMESTAMP,
            last_sell_at TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    
    # Indexes on user_flips
    op.execute("CREATE INDEX IF NOT EXISTS idx_flips_status ON user_flips(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_flips_item ON user_flips(item_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_flips_account ON user_flips(account_id)")
    
    # 4. User settings table (WITHOUT profit_take_pct and loss_refill_pct, which are in 009)
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS user_settings (
            id {pk_type},
            account_id INTEGER NOT NULL UNIQUE,
            available_cash BIGINT DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    
    # 5. Flip transactions table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS flip_transactions (
            id {pk_type},
            flip_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            mutation_type TEXT,
            quantity INTEGER,
            price INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (flip_id) REFERENCES user_flips(id)
        )
    """)
    
    # 6. Price history table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS price_history (
            id {pk_type},
            item_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            price_high INTEGER,
            price_low INTEGER,
            volume_high INTEGER,
            volume_low INTEGER,
            UNIQUE(item_id, timestamp),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS idx_price_history_item_time ON price_history(item_id, timestamp DESC)")
    
    # 7. Price polling metadata table
    op.execute("""
        CREATE TABLE IF NOT EXISTS price_polling_metadata (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            enabled BOOLEAN DEFAULT TRUE,
            last_poll_timestamp INTEGER,
            last_poll_time TIMESTAMP,
            total_snapshots INTEGER DEFAULT 0,
            last_item_sync_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default metadata row
    op.execute("""
        INSERT INTO price_polling_metadata (id, enabled) 
        VALUES (1, TRUE)
        ON CONFLICT (id) DO NOTHING
    """)
    
    # 8. Item conversions table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS item_conversions (
            id {pk_type},
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            conversion_rate_per_hour INTEGER,
            skill_required TEXT,
            level_required INTEGER,
            members BOOLEAN DEFAULT TRUE,
            wiki_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 9. Conversion items table
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS conversion_items (
            id {pk_type},
            conversion_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity NUMERIC NOT NULL DEFAULT 1,
            is_input BOOLEAN NOT NULL,
            FOREIGN KEY (conversion_id) REFERENCES item_conversions(id)
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS idx_conv_items_cid ON conversion_items(conversion_id)")
    
    # Insert default account if none exist
    op.execute("INSERT INTO accounts (name) VALUES ('Main') ON CONFLICT (name) DO NOTHING")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS conversion_items")
    op.execute("DROP TABLE IF EXISTS item_conversions")
    op.execute("DROP TABLE IF EXISTS price_polling_metadata")
    op.execute("DROP TABLE IF EXISTS price_history")
    op.execute("DROP TABLE IF EXISTS flip_transactions")
    op.execute("DROP TABLE IF EXISTS user_settings")
    op.execute("DROP TABLE IF EXISTS user_flips")
    op.execute("DROP TABLE IF EXISTS items")
    op.execute("DROP TABLE IF EXISTS accounts")
