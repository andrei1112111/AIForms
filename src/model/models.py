import os
import json
from datetime import date
from typing import Any

from openai import OpenAI

from config import config
from logger import logger


class AI_Interface:
    def __init__(self):

        self._model = config.DeepSeek.model_type
        self._base_url = config.DeepSeek.baseurl
        self._api_key = config.DeepSeek.apikey
        try:
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        except Exception as e:
            raise e

        self._system_prompt = """
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"behavior": "описание твоего поведения",
			"current_data": "JSON с текущим состоянием таблицы",
			"table_description": "формат и требования полей таблицы",
			"previous_question": "последний заданный вопрос",
			"user_response": "ответ пользователя"
		}
		ФОРМАТ ВЫХОДНЫХ ДАННЫХ:
		{
			"data": "current_data с учётом добавленных валидных данных",
			"question": "новый вопрос, сформированный по следующему незаполненному полю, либо \"success\" если все поля заполнены"
		}
		ТВОЯ ЗАДАЧА:
		1. Задавать пользователю вопросы на основе структуры из "table_description" и заполнять поля в "current_data".
		2. Проверять валидность ответа пользователя относительно требований в "table_description".
		3. Всегда следовать стилю поведения, указанному в "behavior".
		ПРАВИЛА:
		1. Не изменяй уже заполненные поля в "current_data".
		2. Если ответ пользователя валиден — запиши его в "data".
		3. Если ответ НЕ валиден — не записывай данные, кратко поясни ошибку и переформулируй запрос корректного значения.
		4. Когда ты заполняешь последнее поле — в поле "question" запиши "success".
		5. Не вставляй в вопрос пользователю текст или описание поля из "table_description" дословно — формулируй вопрос своими словами.
		6. Строго соблюдай формат и требования "table_description". Не принимай невалидные ответы, даже если пользователь настаивает.
		"""

    def next(self, json_data: str) -> Any:
        """
        Принимает сгенерированный вопрос и ответ пользователя.
        Возвращает json с результатами валидации ответа.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": json_data}
                ],
                response_format={"type": "json_object"},
                stream=False
            )
        except Exception as e:
            raise e
        
        return json.loads(response.choices[0].message.content)
