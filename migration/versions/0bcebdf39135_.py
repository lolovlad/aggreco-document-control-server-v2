"""empty message

Revision ID: 0bcebdf39135
Revises: ffb8fe357d29
Create Date: 2024-10-22 20:34:56.598230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bcebdf39135'
down_revision: Union[str, None] = 'ffb8fe357d29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('claim', sa.Column('id_accident', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'claim', 'accident', ['id_accident'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'claim', type_='foreignkey')
    op.drop_column('claim', 'id_accident')
    # ### end Alembic commands ###
