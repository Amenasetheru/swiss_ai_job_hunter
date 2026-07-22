"""initial baseline

Revision ID: 88cc65105256
Revises:
Create Date: 2026-07-21 18:57:28.879111

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "88cc65105256"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
