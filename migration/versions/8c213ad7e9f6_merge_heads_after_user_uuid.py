"""merge heads after user uuid

Revision ID: 8c213ad7e9f6
Revises: ba7c88a7739a, convert_user_fk_to_uuid
Create Date: 2026-03-10 17:20:31.596238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c213ad7e9f6'
down_revision: Union[str, None] = ('ba7c88a7739a', 'convert_user_fk_to_uuid')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
