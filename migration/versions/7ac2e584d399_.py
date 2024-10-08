"""empty message

Revision ID: 7ac2e584d399
Revises: ae93a80860c5
Create Date: 2024-08-27 18:33:01.019676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ac2e584d399'
down_revision: Union[str, None] = 'ae93a80860c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('equipment_code_key', 'equipment', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('equipment_code_key', 'equipment', ['code'])
    # ### end Alembic commands ###
