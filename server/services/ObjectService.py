from fastapi import Depends, UploadFile
from ..models.Object import *
from ..models.User import UserGet
from ..tables import Object, StateObject as StateObjectORM, Equipment, TypeEquipment, Region as RegionORM

from ..repositories.ObjectRepository import ObjectRepository
from ..repositories import UserRepository, EquipmentRepository
import csv
from io import StringIO
from typing import Dict


class ObjectService:
    def __init__(self,
                 object_repo: ObjectRepository = Depends(),
                 user_repo: UserRepository = Depends(),
                 equipment_repo: EquipmentRepository = Depends()
                 ):
        self.__user_repo: UserRepository = user_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__equipment_repo: EquipmentRepository = equipment_repo
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def is_user_in_object(self, user: UserGet, uuid_object: str) -> bool:
        obj = await self.__object_repo.get_object_by_user_uuid(user.uuid)

        set_uuid = set([i.uuid for i in obj])
        if obj is None:
            return False
        return uuid_object in set_uuid

    async def is_user_in_object_by_uuid_equipment(self, user: UserGet, uuid_equipment: str) -> bool:
        obj = await self.__object_repo.get_object_by_uuid_equipment(user.uuid, uuid_equipment)
        if obj is None:
            return False
        return True

    async def get_count_page(self) -> int:
        count_row = await self.__object_repo.count_row()
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_object(self, num_page: int) -> list[GetObject]:
        start = (num_page - 1) * self.__count_item
        entity = await self.__object_repo.get_limit_object(start, self.__count_item)
        objects = [GetObject.model_validate(entity, from_attributes=True) for entity in entity]
        return objects

    async def get_all_object(self, user: UserGet) -> list[GetObject]:
        if user.type.name != "user":
            filter_user = 0
        else:
            user = await self.__user_repo.get_user_by_uuid(user.uuid)
            filter_user = user.id

        entity = await self.__object_repo.get_all_object(filter_user)
        objects = [GetObject.model_validate(entity, from_attributes=True) for entity in entity]
        return objects

    async def create_object(self, object_target: PostObject):
        entity = Object(
            name=object_target.name,
            address=object_target.address,
            cx=object_target.cx,
            cy=object_target.cy,
            description=object_target.description,
            counterparty=object_target.counterparty,
            id_state=object_target.id_state,
        )
        try:
            await self.__object_repo.add(entity)
        except Exception:
            raise Exception

    async def get_one(self, uuid: str) -> GetObject:
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            return entity
        return GetObject.model_validate(entity, from_attributes=True)

    async def update_object(self, uuid: str, target: UpdateObject):
        entity = await self.__object_repo.get_by_uuid(uuid)

        target_dict = target.model_dump()

        for i in target_dict:
            setattr(entity, i, target_dict[i])
        try:
            await self.__object_repo.update(entity)
        except Exception:
            raise Exception

    async def delete_object(self, uuid: str):
        try:
            await self.__object_repo.delete(uuid)
        except Exception:
            raise Exception

    async def get_users_object(self, uuid: str) -> list[UserGet]:
        entity = await self.__object_repo.get_user_by_uuid_object(uuid)
        users = [UserGet.model_validate(entity, from_attributes=True) for entity in entity]
        return users

    async def registrate_user(self, uuid_object: str, uuid_user: str) -> bool:
        is_add = await self.__object_repo.unique_object_to_user(uuid_object, uuid_user)

        if is_add:
            user = await self.__user_repo.get_user_by_uuid(uuid_user)
            obj = await self.__object_repo.get_by_uuid(uuid_object)
            if user.type.name == "user":
                try:
                    await self.__object_repo.add_user_to_object(obj, user)
                    return True
                except Exception:
                    raise Exception
            else:
                return False
        return False

    async def delete_user_in_object(self, uuid_object: str, uuid_user: str):
        try:
            await self.__object_repo.delete_user_to_object(uuid_object, uuid_user)
        except Exception:
            raise Exception

    async def get_object_to_user(self, uuid_user: str) -> list[GetObject] | None:
        obj = await self.__object_repo.get_object_by_user_uuid(uuid_user)
        if obj is None:
            return obj
        return [GetObject.model_validate(i, from_attributes=True) for i in obj]

    async def _parse_csv_to_keys_id_name(self, file_content: bytes, object_id: int) -> Dict[str, KeyIdNameMapping]:
        """
        Парсит CSV файл в формате:
        Property~Id~Id;Property~Полное имя~FullName
        id1;name1
        id2;name2
        ...
        Ищет equipment в БД по частям имени (для вложенных имен типа "СУЭС.Секция_1")
        Возвращает словарь {id: KeyIdNameMapping}
        """
        try:
            buffer = StringIO(file_content.decode('utf-8-sig'))
            lines = buffer.readlines()
            
            if len(lines) < 2:
                raise ValueError("CSV файл должен содержать заголовок и хотя бы одну строку данных")
            
            # Парсим заголовок
            header_line = lines[0].strip()
            headers = [h.strip() for h in header_line.split(';')]
            
            if len(headers) < 2:
                raise ValueError("CSV файл должен содержать минимум 2 колонки")
            
            # Извлекаем названия колонок из заголовка
            # Формат: Property~Id~Id;Property~Полное имя~FullName
            # Ищем колонку с Id (может быть в разных вариантах: Id, id, Property~Id~Id)
            id_column = None
            name_column = None
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                # Проверяем на наличие Id в заголовке
                if 'id' in header_lower and ('property' in header_lower or id_column is None):
                    id_column = i
                # Проверяем на наличие имени (имя, name, fullname)
                if ('имя' in header_lower or 'name' in header_lower or 'fullname' in header_lower) and name_column is None:
                    name_column = i
            
            # Если не нашли по ключевым словам, используем первую и вторую колонки
            if id_column is None:
                id_column = 0
            if name_column is None:
                name_column = 1
            
            if id_column == name_column:
                raise ValueError("CSV файл должен содержать разные колонки для Id и имени")
            
            # Парсим данные
            keys_id_name = {}
            for line_num, line in enumerate(lines[1:], start=2):
                line = line.strip()
                if not line:
                    continue
                
                values = [v.strip() for v in line.split(';')]
                if len(values) < max(id_column, name_column) + 1:
                    raise ValueError(f"Строка {line_num}: недостаточно колонок (ожидается минимум {max(id_column, name_column) + 1}, получено {len(values)})")
                
                key = values[id_column]
                orig_name = values[name_column]
                
                if not key:
                    raise ValueError(f"Строка {line_num}: пустое значение Id")
                if not orig_name:
                    raise ValueError(f"Строка {line_num}: пустое значение имени")
                
                # Проверяем на дубликаты ключей
                if key in keys_id_name:
                    raise ValueError(f"Строка {line_num}: дублирующийся ключ '{key}'")
                
                # Ищем equipment по частям имени
                # Разбиваем имя по точкам и другим разделителям для поиска вложенности
                name_parts = []
                # Разбиваем по точкам
                if '.' in orig_name:
                    name_parts = [part.strip() for part in orig_name.split('.') if part.strip()]
                else:
                    # Если нет точек, используем все имя
                    name_parts = [orig_name.strip()] if orig_name.strip() else []
                
                # Ищем equipment в БД
                equipment = None
                if name_parts:
                    equipment = await self.__equipment_repo.find_equipment_by_name_parts(object_id, name_parts)
                
                # Создаем структуру сопоставления (3 поля: equipment_id, field2, orig_name)
                mapping = KeyIdNameMapping(
                    equipment_id=str(equipment.uuid) if equipment else None,
                    field2=None,  # Зарезервировано для будущего использования
                    orig_name=orig_name  # Третье поле: оригинальное название из файла
                )
                
                keys_id_name[key] = mapping
            
            if not keys_id_name:
                raise ValueError("CSV файл не содержит данных")
            
            return keys_id_name
            
        except UnicodeDecodeError:
            raise ValueError("Ошибка декодирования файла. Убедитесь, что файл в кодировке UTF-8")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Ошибка парсинга CSV файла: {str(e)}")

    async def get_settings(self, uuid: str) -> GetObjectSettings:
        """Получает settings объекта. Возвращает модель с None значениями если settings пустые"""
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            raise ValueError("Объект не найден")
        
        # Если settings пустые или None, возвращаем модель с None значениями
        if entity.settings is None or not entity.settings:
            return GetObjectSettings()
        
        try:
            # Получаем keys_id_name из settings
            keys_id_name_data = entity.settings.get("keys_id_name", {})
            
            # Преобразуем keys_id_name из словаря в KeyIdNameMapping
            keys_id_name_mappings = {}
            for key, mapping_data in keys_id_name_data.items():
                if isinstance(mapping_data, dict):
                    keys_id_name_mappings[key] = KeyIdNameMapping(
                        equipment_id=mapping_data.get("equipment_id"),
                        field2=mapping_data.get("field2"),
                        orig_name=mapping_data.get("orig_name", "")
                    )
                else:
                    # Обратная совместимость со старым форматом
                    keys_id_name_mappings[key] = KeyIdNameMapping(
                        equipment_id=None,
                        field2=None,
                        orig_name=str(mapping_data) if mapping_data else ""
                    )
            
            # Создаем GetObjectSettings с данными
            settings_data = {
                "db_host": entity.settings.get("db_host"),
                "db_port": entity.settings.get("db_port"),
                "db_name": entity.settings.get("db_name"),
                "db_user": entity.settings.get("db_user"),
                "db_password": entity.settings.get("db_password"),
                "keys_id_name": keys_id_name_mappings
            }
            
            return GetObjectSettings(**settings_data)
        except Exception as e:
            # Если формат некорректный, возвращаем пустую модель
            return GetObjectSettings()

    async def create_settings(self, uuid: str, settings_post: ObjectSettingsPost, csv_file: UploadFile) -> None:
        """Создает settings для объекта с парсингом CSV файла"""
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            raise ValueError("Объект не найден")
        
        # Проверяем, не существуют ли уже settings
        if entity.settings and entity.settings:
            raise ValueError("Settings уже существуют. Используйте PUT для обновления")
        
        # Читаем и парсим CSV файл с поиском equipment
        file_content = await csv_file.read()
        keys_id_name_mappings = await self._parse_csv_to_keys_id_name(file_content, entity.id)
        await csv_file.close()
        
        # Преобразуем KeyIdNameMapping в словарь для сохранения в БД
        keys_id_name_dict = {}
        for key, mapping in keys_id_name_mappings.items():
            keys_id_name_dict[key] = {
                "equipment_id": mapping.equipment_id,
                "field2": mapping.field2,
                "orig_name": mapping.orig_name  # Третье поле
            }
        
        # Формируем settings
        settings_dict = {
            "db_host": settings_post.db_host,
            "db_port": settings_post.db_port,
            "db_name": settings_post.db_name,
            "db_user": settings_post.db_user,
            "db_password": settings_post.db_password,
            "keys_id_name": keys_id_name_dict
        }
        
        entity.settings = settings_dict
        try:
            await self.__object_repo.update(entity)
        except Exception:
            raise Exception("Ошибка сохранения settings")

    async def update_settings(self, uuid: str, settings_update: ObjectSettingsUpdate) -> None:
        """Обновляет settings объекта"""
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            raise ValueError("Объект не найден")
        
        # Получаем текущие settings или создаем пустой словарь
        current_settings = entity.settings if entity.settings else {}
        
        # Обновляем только переданные поля
        update_dict = settings_update.model_dump(exclude_unset=True)
        current_settings.update(update_dict)
        
        entity.settings = current_settings
        try:
            await self.__object_repo.update(entity)
        except Exception:
            raise Exception("Ошибка обновления settings")
