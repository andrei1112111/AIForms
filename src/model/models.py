import os
import json
from datetime import date
from typing import Any

from openai import OpenAI

from config import config
from logger import logger


class AI_Interviewer:
    def __init__(self):
        self._model = config.DeepSeek.model_type
        self._base_url = config.DeepSeek.baseurl
        self._api_key = config.DeepSeek.apikey
        try:
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        except Exception as e:
            raise e

        self._create_question_prompt = """
		О ТЕБЕ:
		Ты помощник для заполнению ответов в опросниках.
		ТВОЯ ЗАДАЧА:
		1. По названию и формату данных генерировать вопрос для пользователя и пример в скобках.
		ПРАВИЛА:
		1. Используй простой и понятный язык.
		2. Формулируй вопросы кратко и по существу.
		3. Вопрос должен содержать призыв к заполнению информации.
		4. Вопрос должен содержать информаци о типе ожидаемых данных.
		6. Избегай двусмысленности.
		7. Ответ должен быть в формате JSON.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"field":  "название поля, по которому нужно сгенерировать вопрос",
			"format": "формат данных, который ожидается для поля"
		}
		ФОРМАТ ОТВЕТА:
		{
			"question": "Сформулированный вопрос"
		}
		"""

        self._change_question_prompt = """
		О ТЕБЕ:
		Ты помощник для заполнению ответов в опросниках.
		Твой предыдущий вопрос был оценен как некоррктный.
		ТВОЯ ЗАДАЧА:
		1. По описанию проблем в твоем вопросе исправить его.
		ПРАВИЛА:
		1. Используй простой и понятный язык.
		2. Формулируй вопросы кратко и по существу.
		3. Вопрос должен содержать призыв к заполнению информации
		4. Вопрос должен содержать информаци о типе ожидаемых данных.
		6. Избегай двусмысленности.
		7. Ответ должен быть в формате JSON.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"field":  "по для которого был сгенерирован вопрос",
			"quetion": "сгенерированный вопрос",
			"issues": "описание проблем вопросом"
		}
		ФОРМАТ ОТВЕТА:
		{
			"question": "Исправленный вопрос"
		}
		"""

        self._change_answer_prompt = """
		О ТЕБЕ:
		Ты эксперт по преобразованию ответов пользователя в нужный формат для опросников.
		ТВОЯ ЗАДАЧА:
		1. Изменить формат ответа на нужный.
		ПРАВИЛА:
		1. Если невозможно изменить формат - ничего не меняй возвращай исходный ответ.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"question": "Вопрос на который ответил пользователь",
			"format":  "Формат, который требуется ответу",
			"answer": "Ответ пользователя"
		}
		ФОРМАТ ОТВЕТА:
		{
			"answer": "Исправленный ответ" или "Исходный ответ"
		}
		"""

    def create_question(self, field: str, format: str) -> str:
        """
        Принимает название поля.
        Возвращает json со сгенерированным вопросом для пользователя.
        """

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": str(self._create_question_prompt)},
                    {"role": "user", "content": '{{ "field": {}, "format": {} }}'.format(field, format)},
                ],
                response_format={"type": "json_object"},
                stream=False,
            )
        except Exception as e:
            raise e

        return json.loads(response.choices[0].message.content)

    def change_question(self, field: str, ai_question: str, issues: str) -> Any:
        """
        Принимает сгенерированный вопрос, поле, и описание проблем с вопросом.
        Возвращает json с исправленным вопросом.
        """

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": str(self._change_question_prompt)},
                    {"role": "user",
                     "content": '{{ "field": {}, "question": {}, "issues": {} }}'.format(field, ai_question, issues)},
                ],
                response_format={"type": "json_object"},
                stream=False,
            )
        except Exception as e:
            raise e

        return json.loads(response.choices[0].message.content)

    def change_answer(self, question: str, format: str, answer: str) -> Any:
        """
        Принимает сгенерированный вопрос, поле, и описание проблем с вопросом.
        Возвращает json с исправленным вопросом.
        """

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": str(self._change_answer_prompt)},
                    {"role": "user",
                     "content": '{{ "question": {}, "format": {}, "answer": {} }}'.format(question, format, answer)},
                ],
                response_format={"type": "json_object"},
                stream=False,
            )
        except Exception as e:
            raise e

        return json.loads(response.choices[0].message.content)


class AI_Validator:
    def __init__(self):

        self._ai_promt = """
		о ТЕБЕ:
		Ты эксперт по валидации даннных.
		На вход ты получаешь название поля и вопрос, который был сгенерирован для пользователя по названию поля.
		ТВОЯ ЗАДАЧА:
		1. Проверить, что вопрос соответствует названию поля.
		ПРАВИЛА:
		1. Ответы на русском языке
		ц. Ответ возврщай в формате JSON со следующей структурой.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"field":  "название поля",
			"question": "вопрос, сгенерированный для пользователя"
		}
		ФОРМАТ ОТВЕТА:
		{
			"staus": "ok" или "failed",
			"issues": "Описание проблем с вопросом" или "" 
		}
		"""

        self._user_promt = """
		о ТЕБЕ:
		Ты эксперт по валидации даннных.
		На вход ты получаешь вопрос и ответ на этот вопрос.
		ТВОЯ ЗАДАЧА:
		1. Проверить, что ответ соответствует требованиям вопроса.
		ПРАВИЛА:
		1. Ответы только на русском языке.
		2. Ответ возвращай в формате JSON со следующей структурой.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"question":  "вопрос, сгенерированный для пользователя",
			"answer":  "ответ пользователя на этот вопрос"
		}
		ФОРМАТ ОТВЕТА:
		{
			"staus": "ok" или "failed",
			"issues": "Уточнение, что пользователья должен исправить, чтобы ответ был корректен" или "" 
		}
		"""

        self._base_url = config.DeepSeek.baseurl
        self._api_key = config.DeepSeek.apikey
        try:
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        except Exception as e:
            raise e
        self._model = config.DeepSeek.model_type

    def validate_ai_question(self, field: str, ai_question: str) -> Any:
        """
        Принимает название поля и сгенерированный вопрос.
        Возвращает json с результатами валидации вопроса."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": str(self._ai_promt)},
                    {"role": "user", "content": '{{ "field": "{}","question":"{}"}}'.format(field, ai_question)},
                ],
                response_format={"type": "json_object"},
                stream=False
            )
        except Exception as e:
            raise e

        return json.loads(response.choices[0].message.content)

    def validate_user_answer(self, ai_question: str, user_answer: str) -> Any:
        """
        Принимает сгенерированный вопрос и ответ пользователя.
        Возвращает json с результатами валидации ответа.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": str(self._user_promt)},
                    {"role": "user",
                     "content": '{{ "question": "{0}", "answer" : "{1}"}}'.format(ai_question, user_answer)},
                ],
                response_format={"type": "json_object"},
                stream=False
            )
        except Exception as e:
            raise e

        return json.loads(response.choices[0].message.content)


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
        print("INPUT DATA TO DEEPSEEK:")
        print(json_data)
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
        print("DEEPSEEK RESPONSE:")
        print(response.choices[0].message.content)
        return json.loads(response.choices[0].message.content)
