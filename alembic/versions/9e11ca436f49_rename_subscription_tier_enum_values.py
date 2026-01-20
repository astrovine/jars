"""rename_subscription_tier_enum_values

Revision ID: 9e11ca436f49
Revises: 04858647df73
Create Date: 2026-01-16 21:01:29.929809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9e11ca436f49'
down_revision: Union[str, Sequence[str], None] = '04858647df73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE trading_tiers ALTER COLUMN tier_name TYPE text USING tier_name::text")
    
    op.execute("UPDATE trading_tiers SET tier_name = 'plus' WHERE tier_name = 'STANDARD'")
    op.execute("UPDATE trading_tiers SET tier_name = 'business' WHERE tier_name = 'PREMIUM'")
    op.execute("UPDATE trading_tiers SET tier_name = 'free' WHERE tier_name = 'FREE'")
    
    op.execute("DROP TYPE IF EXISTS subscriptiontier CASCADE")
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'plus', 'business')")
    
    op.execute("ALTER TABLE trading_tiers ALTER COLUMN tier_name TYPE subscriptiontier USING tier_name::subscriptiontier")


def downgrade() -> None:
    op.execute("ALTER TABLE trading_tiers ALTER COLUMN tier_name TYPE text USING tier_name::text")
    
    op.execute("UPDATE trading_tiers SET tier_name = 'STANDARD' WHERE tier_name = 'plus'")
    op.execute("UPDATE trading_tiers SET tier_name = 'PREMIUM' WHERE tier_name = 'business'")
    op.execute("UPDATE trading_tiers SET tier_name = 'FREE' WHERE tier_name = 'free'")
    
    op.execute("DROP TYPE IF EXISTS subscriptiontier CASCADE")
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('FREE', 'STANDARD', 'PREMIUM')")
    
    op.execute("ALTER TABLE trading_tiers ALTER COLUMN tier_name TYPE subscriptiontier USING tier_name::subscriptiontier")
