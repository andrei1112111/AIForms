"""
Этот модуль обеспечивает взаимодействие между моделями и базой данных. 
engine выполняет:
 - Поиск данных в базе по SQL запросу от модели sql_generator
 - Обращение к database по SQL запросу с получением ответа
 - Преобразование ответа от database в читаемый текст, используя composer
 - Производит валидацию пользователя через базу данных
"""
from SmartSearch.db import database 
from SmartSearch.model import sql_prompt_generator, ai_composer
from .engine import SearchEngine


engine = SearchEngine(sql_prompt_generator, ai_composer, database) 

sql_prompt_generator.set_db_summary(database.getSummary())

__all__ = [
    "engine"
]
