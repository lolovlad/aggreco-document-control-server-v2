"""
Сервис для анализа логов оборудования с использованием LangChain
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI


from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..repositories.LogMessageErrorRepository import LogMessageErrorRepository
from ..repositories.SummarizeRepository import SummarizeRepository
from ..repositories.EquipmentRepository import EquipmentRepository
from ..repositories.ObjectRepository import ObjectRepository
from ..tables import LogMessageError, Summarize, Object, Equipment
from ..settings import settings


class LogAnalysisService:
    """Сервис для анализа логов оборудования"""
    
    def __init__(
        self,
        log_repository: LogMessageErrorRepository,
        summarize_repository: SummarizeRepository,
        equipment_repository: EquipmentRepository,
        object_repository: ObjectRepository
    ):
        self.log_repository = log_repository
        self.summarize_repository = summarize_repository
        self.equipment_repository = equipment_repository
        self.object_repository = object_repository
        
        # Инициализация LLM через LangChain
        self.llm = None
        if settings.yandex_cloud_api_key:
            if ChatOpenAI is None:
                raise ValueError("ChatOpenAI не найден. Установите langchain-openai: pip install langchain-openai")
            # Yandex Cloud поддерживает OpenAI-совместимый API
            # Используем параметры для совместимости с Yandex Cloud
            self.llm = ChatOpenAI(
                model=settings.yandex_cloud_llm_model,
                api_key=settings.yandex_cloud_api_key,
                base_url="https://llm.api.cloud.yandex.net/v1",
                default_headers={
                    "x-folder-id": settings.yandex_cloud_folder_id
                },
                temperature=0.1,
                reasoning_effort="low"
            )
    
    async def analyze_logs_for_object(self, uuid_object: str) -> Dict[str, Any]:
        """
        Анализирует логи для объекта
        
        Args:
            uuid_object: UUID объекта
            
        Returns:
            Словарь с результатами анализа для каждой машины
        """
        print(f"\n{'='*80}")
        print(f"[Анализ логов] Начало анализа для объекта {uuid_object}")
        print(f"{'='*80}")
        
        # Получаем объект
        object_entity = await self.object_repository.get_by_uuid(uuid_object)
        if not object_entity:
            print(f"[Анализ логов] ОШИБКА: Объект с UUID {uuid_object} не найден")
            raise ValueError(f"Объект с UUID {uuid_object} не найден")
        
        print(f"[Анализ логов] Объект найден: {object_entity.name}")
        
        # Получаем ВСЕ оборудование объекта из БД
        print(f"[Анализ логов] Получение всего оборудования объекта из БД...")
        all_equipment = await self.equipment_repository.get_all_equipment(uuid_object)
        
        if not all_equipment:
            print(f"[Анализ логов] ОШИБКА: Не найдено оборудования для объекта")
            return {"error": "Не найдено оборудования для объекта"}
        
        print(f"[Анализ логов] Найдено оборудования в БД: {len(all_equipment)}")
        
        # Группируем оборудование по общему названию
        # Общее название - это часть до определенного разделителя
        def get_common_name(equipment_name: str) -> str:
            """Извлекает общее название из полного названия оборудования"""
            # Примеры: 
            # "ПС.ПС5.Яч 5А-3 ВВОД3 (Яч 19 ГПЭС).Плакат" -> "ПС.ПС5"
            # "ПС.ПС5.Яч 5А-3 ВВОД3" -> "ПС.ПС5"
            # "ГПГУ.ГПГУ_1" -> "ГПГУ"
            
            # Если есть несколько точек, берем первые две части (например, "ПС.ПС5")
            parts = equipment_name.split('.')
            if len(parts) >= 2:
                # Берем первые две части как общее название
                return '.'.join(parts[:2])
            elif len(parts) == 1:
                # Если только одна часть, но есть скобка - берем до скобки
                if '(' in equipment_name:
                    return equipment_name.split('(')[0].strip()
                # Иначе возвращаем как есть
                return equipment_name
            else:
                return equipment_name
        
        # Группируем оборудование по общему названию
        equipment_groups = {}
        for equipment in all_equipment:
            common_name = get_common_name(equipment.name)
            if common_name not in equipment_groups:
                equipment_groups[common_name] = []
            equipment_groups[common_name].append(equipment)
        
        print(f"[Анализ логов] Сгруппировано в {len(equipment_groups)} групп по общему названию:")
        for common_name, eq_list in equipment_groups.items():
            print(f"    - {common_name}: {len(eq_list)} единиц оборудования")
        
        print(f"{'-'*80}\n")
        
        results = {}
        group_count = 0
        total_groups = len(equipment_groups)
        
        # Обрабатываем каждую группу оборудования
        for common_name, equipment_list in equipment_groups.items():
            group_count += 1
            equipment_ids = [eq.id for eq in equipment_list]
            equipment_names = [eq.name for eq in equipment_list]
            
            print(f"[Группа {group_count}/{total_groups}] Обработка: {common_name}")
            print(f"[Группа {group_count}/{total_groups}] Единиц оборудования в группе: {len(equipment_list)}")
            print(f"[Группа {group_count}/{total_groups}] ID оборудования: {equipment_ids}")
            print(f"[Группа {group_count}/{total_groups}] Названия: {equipment_names}")
            
            # Анализируем логи для этой группы оборудования
            try:
                result = await self._analyze_logs_for_equipment_group(
                    object_entity.id,
                    equipment_ids,
                    common_name,
                    equipment_names
                )
                results[common_name] = result
                print(f"[Группа {group_count}/{total_groups}] ✓ Анализ завершен успешно")
            except Exception as e:
                print(f"[Группа {group_count}/{total_groups}] ✗ ОШИБКА: {str(e)}")
                results[common_name] = {
                    "error": f"Ошибка при анализе логов: {str(e)}"
                }
            print(f"{'-'*80}\n")
        
        print(f"{'='*80}")
        print(f"[Анализ логов] Анализ завершен. Обработано групп оборудования: {group_count}/{total_groups}")
        print(f"{'='*80}\n")
        
        return results
    
    async def _analyze_logs_for_equipment(
        self,
        id_object: int,
        id_equipment: int,
        equipment_name: str
    ) -> Dict[str, Any]:
        """
        Анализирует логи для конкретного оборудования
        
        Args:
            id_object: ID объекта
            id_equipment: ID оборудования
            equipment_name: Название оборудования
            
        Returns:
            Результат анализа с полями text и metadata
        """
        # Получаем необработанные логи
        print(f"  [Шаг 1/5] Получение необработанных логов...")
        logs = await self.log_repository.get_unprocessed_logs_by_object_and_equipment(
            id_object,
            id_equipment
        )
        
        if not logs:
            print(f"  [Шаг 1/5] Нет необработанных логов для анализа")
            return {
                "text": "Нет необработанных логов для анализа",
                "metadata": {}
            }
        
        print(f"  [Шаг 1/5] Получено логов: {len(logs)}")
        
        # Проверяем и получаем Summarize для текущего месяца
        print(f"  [Шаг 2/5] Проверка Summarize для текущего месяца...")
        current_month_summarize = await self.summarize_repository.get_by_object_and_equipment_and_month(
            id_object,
            id_equipment
        )
        
        summarize_text = None
        if current_month_summarize:
            print(f"  [Шаг 2/5] Найден Summarize для текущего месяца, будет использован для контекста")
            summarize_text = current_month_summarize.text
        else:
            print(f"  [Шаг 2/5] Summarize для текущего месяца не найден, будет создан новый")
        
        # Подготавливаем данные логов для LLM
        print(f"  [Шаг 3/5] Подготовка данных логов для LLM...")
        logs_data = []
        log_ids = []
        for log in logs:
            logs_data.append({
                "time": log.create_at.isoformat() if log.create_at else None,
                "message": log.message,
                "class_log_text": log.class_log_text,
                "class_log_int": log.class_log_int,
                "entity_equipment": log.entity_equipment,
                "number_equipment": log.number_equipment,
            })
            log_ids.append(log.id)
        
        print(f"  [Шаг 3/5] Данные подготовлены: {len(logs_data)} записей")
        
        # Вызываем LLM для анализа
        print(f"  [Шаг 4/5] Отправка запроса в LLM для анализа...")
        if not self.llm:
            print(f"  [Шаг 4/5] ОШИБКА: LLM не настроен")
            raise ValueError("LLM не настроен. Проверьте YANDEX_CLOUD_API_KEY в настройках")
        
        analysis_result = await self._analyze_with_llm(logs_data, summarize_text, equipment_name)
        print(f"  [Шаг 4/5] LLM анализ завершен успешно")
        
        # Сохраняем Summarize для текущего месяца
        print(f"  [Шаг 5/5] Сохранение результатов анализа...")
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        if current_month_summarize:
            # Обновляем существующий Summarize текущего месяца
            print(f"  [Шаг 5/5] Обновление существующего Summarize для текущего месяца")
            current_month_summarize.text = analysis_result["text"]
            current_month_summarize.metadata_equipment = analysis_result["metadata"]
            current_month_summarize.datetime_end = now
            await self.summarize_repository.update(current_month_summarize)
            print(f"  [Шаг 5/5] Summarize обновлен")
        else:
            # Создаем новый Summarize для текущего месяца
            print(f"  [Шаг 5/5] Создание нового Summarize для текущего месяца")
            new_summarize = Summarize(
                id_object=id_object,
                id_equipment=id_equipment,
                text=analysis_result["text"],
                metadata_equipment=analysis_result["metadata"],
                datetime_start=month_start,
                datetime_end=now
            )
            await self.summarize_repository.add(new_summarize)
            print(f"  [Шаг 5/5] Summarize создан")
        
        # Помечаем логи как обработанные
        print(f"  [Шаг 5/5] Пометка логов как обработанных ({len(log_ids)} записей)...")
        await self.log_repository.mark_logs_as_processed(log_ids)
        print(f"  [Шаг 5/5] Логи помечены как обработанные")
        
        return analysis_result
    
    async def _analyze_logs_for_equipment_group(
        self,
        id_object: int,
        equipment_ids: list[int],
        common_name: str,
        equipment_names: list[str]
    ) -> Dict[str, Any]:
        """
        Анализирует логи для группы оборудования
        
        Args:
            id_object: ID объекта
            equipment_ids: Список ID оборудования в группе
            common_name: Общее название группы
            equipment_names: Список названий оборудования в группе
            
        Returns:
            Результат анализа с полями text и metadata
        """
        # Получаем необработанные логи для группы оборудования
        print(f"  [Шаг 1/5] Получение необработанных логов для группы оборудования...")
        logs = await self.log_repository.get_unprocessed_logs_by_object_and_equipment_ids(
            id_object,
            equipment_ids
        )
        
        if not logs:
            print(f"  [Шаг 1/5] Нет необработанных логов для группы")
            return {
                "text": "Нет необработанных логов для анализа",
                "metadata": {}
            }
        
        print(f"  [Шаг 1/5] Получено логов: {len(logs)}")
        
        # Проверяем и получаем Summarize для текущего месяца
        # Используем первое оборудование из группы для Summarize
        primary_equipment_id = equipment_ids[0]
        print(f"  [Шаг 2/5] Проверка Summarize для текущего месяца (по оборудованию ID: {primary_equipment_id})...")
        current_month_summarize = await self.summarize_repository.get_by_object_and_equipment_and_month(
            id_object,
            primary_equipment_id
        )
        
        summarize_text = None
        if current_month_summarize:
            print(f"  [Шаг 2/5] Найден Summarize для текущего месяца, будет использован для контекста")
            summarize_text = current_month_summarize.text
        else:
            print(f"  [Шаг 2/5] Summarize для текущего месяца не найден, будет создан новый")
        
        # Подготавливаем данные логов для LLM
        print(f"  [Шаг 3/5] Подготовка данных логов для LLM...")
        logs_data = []
        log_ids = []
        for log in logs:
            logs_data.append({
                "time": log.create_at.isoformat() if log.create_at else None,
                "message": log.message,
                "class_log_text": log.class_log_text,
                "class_log_int": log.class_log_int,
                "entity_equipment": log.entity_equipment,
                "number_equipment": log.number_equipment,
                "equipment_id": log.id_equipment,
            })
            log_ids.append(log.id)
        
        print(f"  [Шаг 3/5] Данные подготовлены: {len(logs_data)} записей")
        
        # Вызываем LLM для анализа
        print(f"  [Шаг 4/5] Отправка запроса в LLM для анализа...")
        if not self.llm:
            print(f"  [Шаг 4/5] ОШИБКА: LLM не настроен")
            raise ValueError("LLM не настроен. Проверьте YANDEX_CLOUD_API_KEY в настройках")
        
        analysis_result = await self._analyze_with_llm_for_group(
            logs_data, 
            summarize_text, 
            common_name,
            equipment_names
        )
        print(f"  [Шаг 4/5] LLM анализ завершен успешно")
        
        # Сохраняем Summarize для текущего месяца
        print(f"  [Шаг 5/5] Сохранение результатов анализа...")
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        if current_month_summarize:
            # Обновляем существующий Summarize текущего месяца
            print(f"  [Шаг 5/5] Обновление существующего Summarize для текущего месяца")
            current_month_summarize.text = analysis_result["text"]
            current_month_summarize.metadata_equipment = analysis_result["metadata"]
            current_month_summarize.datetime_end = now
            await self.summarize_repository.update(current_month_summarize)
            print(f"  [Шаг 5/5] Summarize обновлен")
        else:
            # Создаем новый Summarize для текущего месяца
            print(f"  [Шаг 5/5] Создание нового Summarize для текущего месяца")
            new_summarize = Summarize(
                id_object=id_object,
                id_equipment=primary_equipment_id,
                text=analysis_result["text"],
                metadata_equipment=analysis_result["metadata"],
                datetime_start=month_start,
                datetime_end=now
            )
            await self.summarize_repository.add(new_summarize)
            print(f"  [Шаг 5/5] Summarize создан")
        
        # Помечаем логи как обработанные
        print(f"  [Шаг 5/5] Пометка логов как обработанных ({len(log_ids)} записей)...")
        await self.log_repository.mark_logs_as_processed(log_ids)
        print(f"  [Шаг 5/5] Логи помечены как обработанные")
        
        return analysis_result
    
    async def _analyze_with_llm_for_group(
        self,
        logs: List[Dict[str, Any]],
        summarize_text: Optional[str],
        common_name: str,
        equipment_names: List[str]
    ) -> Dict[str, Any]:
        """
        Анализирует логи через LLM для группы оборудования
        
        Args:
            logs: Список логов
            summarize_text: Текст предыдущего Summarize (если есть)
            common_name: Общее название группы оборудования
            equipment_names: Список названий оборудования в группе
            
        Returns:
            Словарь с полями text (markdown) и metadata (json)
        """
        # Создаем промпт
        system_template = """Ты эксперт по анализу логов промышленного оборудования. 
Проанализируй предоставленные логи и выдели проблемные места оборудования.

Твоя задача:
1. Определить проблемные места оборудования
2. Выявить что происходит постоянно
3. Определить в каких узлах проблемы
4. Проанализировать частые сообщения об ошибках

ВАЖНО: Анализируй логи для группы оборудования с общим названием "{common_name}".
В группу входят следующие единицы оборудования: {equipment_names}

В ответе предоставь:
1. Текстовый анализ в формате Markdown с описанием проблем
2. Структурированные данные в JSON формате для отображения в виде тегов (самые частые сообщения об ошибках, проблемные узлы, статистика)

ВАЖНО: Отвечай ТОЛЬКО валидным JSON в следующем формате:
{{
    "text": "Markdown текст с анализом",
    "metadata": {{
        "most_frequent_errors": ["ошибка 1", "ошибка 2"],
        "problematic_nodes": ["узел 1", "узел 2"],
        "recurring_issues": ["проблема 1", "проблема 2"],
        "statistics": {{
            "total_logs": 100,
            "error_count": 50,
            "warning_count": 30
        }}
    }}
}}
"""
        
        human_template = """Проанализируй логи для группы оборудования "{common_name}".

ЕДИНИЦЫ ОБОРУДОВАНИЯ В ГРУППЕ:
{equipment_names_list}

ЛОГИ ДЛЯ АНАЛИЗА:
{logs_json}

{summarize_section}

Проанализируй эти логи для всей группы оборудования и предоставь детальный анализ в формате JSON с полями text (markdown) и metadata (структурированные данные).
"""
        
        # Формируем секцию Summarize
        summarize_section = ""
        if summarize_text:
            summarize_section = f"\nПРЕДЫДУЩИЙ АНАЛИЗ (Summarize):\n{summarize_text}\n\nИспользуй этот анализ для контекста."
        
        # Преобразуем логи в JSON
        logs_json = json.dumps(logs, ensure_ascii=False, indent=2, default=str)
        
        # Формируем список названий оборудования
        equipment_names_list = "\n".join([f"- {name}" for name in equipment_names])
        
        # Создаем промпт шаблон
        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        
        # Создаем цепочку
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Выполняем запрос
        print(f"      → Отправка запроса в LLM (модель: {settings.yandex_cloud_llm_model})...")
        result = await chain.ainvoke({
            "common_name": common_name,
            "equipment_names": equipment_names,
            "equipment_names_list": equipment_names_list,
            "logs_json": logs_json,
            "summarize_section": summarize_section
        })
        print(f"      → Получен ответ от LLM")
        
        # Проверяем формат результата
        if isinstance(result, dict):
            # Убеждаемся, что есть нужные поля
            if "text" not in result:
                result["text"] = "Анализ выполнен"
            if "metadata" not in result:
                result["metadata"] = {}
            return result
        else:
            # Если результат не словарь, пытаемся его распарсить
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    result = {"text": result, "metadata": {}}
            return {"text": str(result), "metadata": {}}
    
    async def _analyze_with_llm(
        self,
        logs: List[Dict[str, Any]],
        summarize_text: Optional[str],
        equipment_name: str
    ) -> Dict[str, Any]:
        """
        Анализирует логи через LLM с использованием LangChain
        
        Args:
            logs: Список логов
            summarize_text: Текст предыдущего Summarize (если есть)
            equipment_name: Название оборудования
            
        Returns:
            Словарь с полями text (markdown) и metadata (json)
        """
        # Создаем промпт
        system_template = """Ты эксперт по анализу логов промышленного оборудования. 
Проанализируй предоставленные логи и выдели проблемные места оборудования.

Твоя задача:
1. Определить проблемные места оборудования
2. Выявить что происходит постоянно
3. Определить в каких узлах проблемы
4. Проанализировать частые сообщения об ошибках

В ответе предоставь:
1. Текстовый анализ в формате Markdown с описанием проблем
2. Структурированные данные в JSON формате для отображения в виде тегов (самые частые сообщения об ошибках, проблемные узлы, статистика)

ВАЖНО: Отвечай ТОЛЬКО валидным JSON в следующем формате:
{{
    "text": "Markdown текст с анализом",
    "metadata": {{
        "most_frequent_errors": ["ошибка 1", "ошибка 2"],
        "problematic_nodes": ["узел 1", "узел 2"],
        "recurring_issues": ["проблема 1", "проблема 2"],
        "statistics": {{
            "total_logs": 100,
            "error_count": 50,
            "warning_count": 30
        }}
    }}
}}
"""
        
        human_template = """Проанализируй логи оборудования "{equipment_name}".

ЛОГИ ДЛЯ АНАЛИЗА:
{logs_json}

{summarize_section}

Проанализируй эти логи и предоставь детальный анализ в формате JSON с полями text (markdown) и metadata (структурированные данные).
"""
        
        # Формируем секцию Summarize
        summarize_section = ""
        if summarize_text:
            summarize_section = f"\nПРЕДЫДУЩИЙ АНАЛИЗ (Summarize):\n{summarize_text}\n\nИспользуй этот анализ для контекста."
        
        # Преобразуем логи в JSON
        logs_json = json.dumps(logs, ensure_ascii=False, indent=2, default=str)
        
        # Создаем промпт шаблон
        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        
        # Создаем цепочку
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        # Выполняем запрос
        print(f"      → Отправка запроса в LLM (модель: {settings.yandex_cloud_llm_model})...")
        result = await chain.ainvoke({
            "equipment_name": equipment_name,
            "logs_json": logs_json,
            "summarize_section": summarize_section
        })
        print(f"      → Получен ответ от LLM")
        
        # Проверяем формат результата
        if isinstance(result, dict):
            # Убеждаемся, что есть нужные поля
            if "text" not in result:
                result["text"] = "Анализ выполнен"
            if "metadata" not in result:
                result["metadata"] = {}
            return result
        else:
            # Если результат не словарь, пытаемся его распарсить
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    result = {"text": result, "metadata": {}}
            return {"text": str(result), "metadata": {}}
