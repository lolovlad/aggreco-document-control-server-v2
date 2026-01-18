"""
Сервис для работы с Summarize
"""
from typing import Optional, List
from datetime import datetime

from ..repositories.SummarizeRepository import SummarizeRepository
from ..repositories.EquipmentRepository import EquipmentRepository
from ..repositories.ObjectRepository import ObjectRepository
from ..models.Summarize import GetSummarize
from ..tables import Summarize


class SummarizeService:
    """Сервис для работы с Summarize"""
    
    def __init__(
        self,
        summarize_repository: SummarizeRepository,
        equipment_repository: EquipmentRepository,
        object_repository: ObjectRepository
    ):
        self.summarize_repository = summarize_repository
        self.equipment_repository = equipment_repository
        self.object_repository = object_repository
    
    async def get_summarize_by_object(
        self,
        uuid_object: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[GetSummarize]:
        """
        Получить все Summarize для объекта с фильтрацией по датам
        
        Args:
            uuid_object: UUID объекта
            start_date: Начальная дата в формате YYYY-MM-DD (опционально)
            end_date: Конечная дата в формате YYYY-MM-DD (опционально)
            
        Returns:
            Список Summarize с информацией об оборудовании
        """
        # Получаем объект
        object_entity = await self.object_repository.get_by_uuid(uuid_object)
        if not object_entity:
            raise ValueError(f"Объект с UUID {uuid_object} не найден")
        
        # Преобразуем строки дат в datetime
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Неверный формат start_date: {start_date}. Используйте YYYY-MM-DD")
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Неверный формат end_date: {end_date}. Используйте YYYY-MM-DD")
        
        # Получаем Summarize
        summarize_list = await self.summarize_repository.get_by_object(
            object_entity.id,
            start_datetime,
            end_datetime
        )
        
        # Загружаем информацию об оборудовании для каждого Summarize
        result = []
        equipment_cache = {}
        
        for summarize in summarize_list:
            # Получаем оборудование из кэша или БД
            if summarize.id_equipment not in equipment_cache:
                equipment = await self.equipment_repository.get_equipment_by_ids([summarize.id_equipment])
                if equipment:
                    equipment_cache[summarize.id_equipment] = equipment[0]
                else:
                    equipment_cache[summarize.id_equipment] = None
            
            equipment = equipment_cache[summarize.id_equipment]
            
            # Создаем модель ответа
            from ..models.Equipment import GetEquipment
            equipment_model = None
            equipment_uuid = None
            equipment_name = None
            
            if equipment:
                equipment_model = GetEquipment.model_validate(equipment, from_attributes=True)
                equipment_uuid = str(equipment.uuid)
                equipment_name = equipment.name
            
            summarize_model = GetSummarize.model_validate(summarize, from_attributes=True)
            summarize_model.equipment = equipment_model
            summarize_model.equipment_uuid = equipment_uuid
            summarize_model.equipment_name = equipment_name
            
            result.append(summarize_model)
        
        return result
    
    async def get_summarize_by_object_and_equipment(
        self,
        uuid_object: str,
        uuid_equipment: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[GetSummarize]:
        """
        Получить все Summarize для объекта и оборудования с фильтрацией по датам
        
        Args:
            uuid_object: UUID объекта
            uuid_equipment: UUID оборудования
            start_date: Начальная дата в формате YYYY-MM-DD (опционально)
            end_date: Конечная дата в формате YYYY-MM-DD (опционально)
            
        Returns:
            Список Summarize с информацией об оборудовании
        """
        # Получаем объект и оборудование
        object_entity = await self.object_repository.get_by_uuid(uuid_object)
        if not object_entity:
            raise ValueError(f"Объект с UUID {uuid_object} не найден")
        
        equipment = await self.equipment_repository.get_by_uuid(uuid_equipment)
        if not equipment:
            raise ValueError(f"Оборудование с UUID {uuid_equipment} не найдено")
        
        # Преобразуем строки дат в datetime
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Неверный формат start_date: {start_date}. Используйте YYYY-MM-DD")
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Неверный формат end_date: {end_date}. Используйте YYYY-MM-DD")
        
        # Получаем Summarize
        summarize_list = await self.summarize_repository.get_by_object_and_equipment(
            object_entity.id,
            equipment.id,
            start_datetime,
            end_datetime
        )
        
        # Создаем модели ответа
        from ..models.Equipment import GetEquipment
        equipment_model = GetEquipment.model_validate(equipment, from_attributes=True)
        
        result = []
        for summarize in summarize_list:
            summarize_model = GetSummarize.model_validate(summarize, from_attributes=True)
            summarize_model.equipment = equipment_model
            summarize_model.equipment_uuid = str(equipment.uuid)
            summarize_model.equipment_name = equipment.name
            result.append(summarize_model)
        
        return result
