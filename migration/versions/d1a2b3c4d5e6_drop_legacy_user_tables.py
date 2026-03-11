"""drop legacy user-related tables

Revision ID: d1a2b3c4d5e6
Revises: 8c213ad7e9f6
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4d5e6"
down_revision: Union[str, None] = "8c213ad7e9f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Удаляем старые таблицы, связанные с локальной моделью пользователей:
    - user
    - type_user
    - profession

    Все внешние ключи на них были убраны в миграции convert_user_fk_to_uuid,
    поэтому здесь можно безопасно дропнуть таблицы.
    """
    # Удаляем оставшиеся зависимости от таблицы user
    # user_to_document: старый FK id_user -> user.id больше не нужен
    with op.batch_alter_table("user_to_document") as batch_op:
        try:
            batch_op.drop_constraint("user_to_document_id_user_fkey", type_="foreignkey")
        except Exception:
            # Если ограничения уже нет (например, на свежей БД) — игнорируем
            pass
        try:
            batch_op.drop_column("id_user")
        except Exception:
            # Если колонка уже удалена — игнорируем
            pass

    op.drop_table("user")
    op.drop_table("type_user")
    op.drop_table("profession")


def downgrade() -> None:
    """
    Обратное применение миграции не поддерживается, так как восстановление
    структуры и данных старых таблиц пользователей не требуется.
    """
    raise RuntimeError("Downgrade is not supported for drop_legacy_user_tables")

