"""convert object/equipment foreign keys to UUID and drop legacy tables

Revision ID: obj_equip_fk_to_uuid
Revises: d1a2b3c4d5e6
Create Date: 2026-03-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "obj_equip_fk_to_uuid"
down_revision: Union[str, None] = "d1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Миграция по аналогии с convert_user_fk_to_uuid, но для object/equipment.

    Шаги:
    1. Добавляем временные UUID-колонки в таблицы, где есть id_object / id_equipment.
    2. Переносим значения uuid из таблиц object / equipment.
    3. Удаляем внешние ключи и старые integer-поля, переименовываем *_uuid в окончательные имена.
    4. Удаляем старые таблицы object / equipment / object_to_user / equipment_to_accident.
    """

    # 1. Добавляем UUID-колонки с целевыми именами uuid_object / uuid_equipment
    op.add_column(
        "accident",
        sa.Column("uuid_object", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "technical_proposals",
        sa.Column("uuid_object", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "log_messages_error",
        sa.Column("uuid_object", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "log_messages_error",
        sa.Column("uuid_equipment", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "summatize",
        sa.Column("uuid_object", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "summatize",
        sa.Column("uuid_equipment", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "equipment_to_accident",
        sa.Column("uuid_equipment", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Переносим UUID из object / equipment
    # accident.id_object -> accident.uuid_object
    op.execute(
        """
        UPDATE accident a
        SET uuid_object = o.uuid
        FROM "object" o
        WHERE a.id_object = o.id
        """
    )

    # technical_proposals.id_object -> technical_proposals.uuid_object
    op.execute(
        """
        UPDATE technical_proposals tp
        SET uuid_object = o.uuid
        FROM "object" o
        WHERE tp.id_object = o.id
        """
    )

    # log_messages_error.id_object / id_equipment -> uuid_*
    op.execute(
        """
        UPDATE log_messages_error l
        SET uuid_object = o.uuid
        FROM "object" o
        WHERE l.id_object = o.id
        """
    )
    op.execute(
        """
        UPDATE log_messages_error l
        SET uuid_equipment = e.uuid
        FROM equipment e
        WHERE l.id_equipment = e.id
        """
    )

    # summatize.id_object / id_equipment -> uuid_*
    op.execute(
        """
        UPDATE summatize s
        SET uuid_object = o.uuid
        FROM "object" o
        WHERE s.id_object = o.id
        """
    )
    op.execute(
        """
        UPDATE summatize s
        SET uuid_equipment = e.uuid
        FROM equipment e
        WHERE s.id_equipment = e.id
        """
    )

    # equipment_to_accident.id_equipment -> uuid_equipment
    op.execute(
        """
        UPDATE equipment_to_accident eta
        SET uuid_equipment = e.uuid
        FROM equipment e
        WHERE eta.id_equipment = e.id
        """
    )

    # 3. Удаляем внешние ключи и старые integer-поля

    # accident
    try:
        op.drop_constraint("accident_id_object_fkey", "accident", type_="foreignkey")
    except Exception:
        pass
    with op.batch_alter_table("accident") as batch_op:
        try:
            batch_op.drop_column("id_object")
        except Exception:
            pass

    # technical_proposals
    try:
        op.drop_constraint(
            "technical_proposals_id_object_fkey",
            "technical_proposals",
            type_="foreignkey",
        )
    except Exception:
        pass
    with op.batch_alter_table("technical_proposals") as batch_op:
        try:
            batch_op.drop_column("id_object")
        except Exception:
            pass

    # log_messages_error
    try:
        op.drop_constraint(
            "log_messages_error_id_object_fkey",
            "log_messages_error",
            type_="foreignkey",
        )
    except Exception:
        pass
    try:
        op.drop_constraint(
            "log_messages_error_id_equipment_fkey",
            "log_messages_error",
            type_="foreignkey",
        )
    except Exception:
        pass
    with op.batch_alter_table("log_messages_error") as batch_op:
        try:
            batch_op.drop_column("id_object")
        except Exception:
            pass
        try:
            batch_op.drop_column("id_equipment")
        except Exception:
            pass

    # summatize
    try:
        op.drop_constraint("summatize_id_object_fkey", "summatize", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_constraint(
            "summatize_id_equipment_fkey", "summatize", type_="foreignkey"
        )
    except Exception:
        pass
    with op.batch_alter_table("summatize") as batch_op:
        try:
            batch_op.drop_column("id_object")
        except Exception:
            pass
        try:
            batch_op.drop_column("id_equipment")
        except Exception:
            pass

    # equipment_to_accident
    try:
        op.drop_constraint(
            "equipment_to_accident_id_equipment_fkey",
            "equipment_to_accident",
            type_="foreignkey",
        )
    except Exception:
        pass
    with op.batch_alter_table("equipment_to_accident") as batch_op:
        try:
            batch_op.drop_column("id_equipment")
        except Exception:
            pass
        # колонка uuid_equipment остается как основная UUID-ссылка

    # 4. Удаляем старые таблицы object / equipment / object_to_user
    # Внешние ключи на них к этому моменту уже сняты.
    try:
        op.drop_table("object_to_user")
    except Exception:
        pass
    try:
        op.drop_table("equipment")
    except Exception:
        pass
    try:
        op.drop_table("object")
    except Exception:
        pass


def downgrade() -> None:
    """
    Обратное применение миграции не поддерживается, так как восстановление
    целостных integer-ссылок на удалённые таблицы object/equipment невозможно.
    """
    raise RuntimeError("Downgrade is not supported for convert_object_equipment_fk_to_uuid")

