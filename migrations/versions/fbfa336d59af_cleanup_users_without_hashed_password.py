"""cleanup users without hashed_password

Revision ID: fbfa336d59af
Revises: 244ddc180f58
Create Date: 2026-09-21 12:37:48.012786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fbfa336d59af'
down_revision: Union[str, Sequence[str], None] = '244ddc180f58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(text("Delete from users where hashed_password is NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError("Cant be implemented")
