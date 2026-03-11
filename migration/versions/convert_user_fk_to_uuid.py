"""convert user foreign keys to user uuid

Revision ID: convert_user_fk_to_uuid
Revises: ae93a80860c5
Create Date: 2026-03-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "convert_user_fk_to_uuid"
down_revision: Union[str, None] = "ae93a80860c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # object_to_user: меняем id_user (FK -> user.id) на user_uuid (uuid, PK)
    op.add_column(
        "object_to_user",
        sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE object_to_user otu
        SET user_uuid = u.uuid
        FROM "user" u
        WHERE otu.id_user = u.id
        """
    )
    op.alter_column("object_to_user", "user_uuid", nullable=False)
    op.drop_constraint("object_to_user_id_user_fkey", "object_to_user", type_="foreignkey")
    op.drop_column("object_to_user", "id_user")

    # claim: id_user -> user_uuid
    op.add_column(
        "claim",
        sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE claim c
        SET user_uuid = u.uuid
        FROM "user" u
        WHERE c.id_user = u.id
        """
    )
    op.alter_column("claim", "user_uuid", nullable=True)
    op.drop_constraint("claim_id_user_fkey", "claim", type_="foreignkey")
    op.drop_column("claim", "id_user")

    # technical_proposals: id_user -> user_uuid, id_expert -> expert_uuid
    op.add_column(
        "technical_proposals",
        sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "technical_proposals",
        sa.Column("expert_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE technical_proposals tp
        SET user_uuid = u.uuid
        FROM "user" u
        WHERE tp.id_user = u.id
        """
    )
    op.execute(
        """
        UPDATE technical_proposals tp
        SET expert_uuid = u.uuid
        FROM "user" u
        WHERE tp.id_expert = u.id
        """
    )
    op.drop_constraint("technical_proposals_id_user_fkey", "technical_proposals", type_="foreignkey")
    op.drop_constraint("technical_proposals_id_expert_fkey", "technical_proposals", type_="foreignkey")
    op.drop_column("technical_proposals", "id_user")
    op.drop_column("technical_proposals", "id_expert")


def downgrade() -> None:
    raise RuntimeError("Downgrade is not supported for convert_user_fk_to_uuid")

