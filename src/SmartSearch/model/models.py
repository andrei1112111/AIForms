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

		self._create_answer_prompt = """
		О ТЕБЕ:
		Ты помощник для заполнению ответов в опросниках.
		ТВОЯ ЗАДАЧА:
		1. По названию поля генерировать вопрос для пользователя.
		ПРАВИЛА:
		1. Используй простой и понятный язык.
		2. Формулируй вопросы кратко и по существу.
		3. Вопрос должен содержать призыв к заполнению информации.
		4. Вопрос должен содержать информаци о типе ожидаемых данных.
		6. Избегай двусмысленности.
		7. Ответ должен быть в формате JSON.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"field":  "название поля, по которому нужно сгенерировать вопрос"
		}
		ФОРМАТ ОТВЕТА:
		{
			"question": "Сформулированный вопрос"
		}
		"""

		
		self._change_answer_prompt = """
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
	

	def create_answer(self, field: str) -> str:
		"""
		Принимает название поля.
		Возвращает json со сгенерированным вопросом для пользователя.
		"""
		
		try:
			response = self._client.chat.completions.create(
				model=self._model,
				messages=[
					{"role": "system", "content": str(self._create_answer_prompt)},
					{"role": "user", "content": '{ "field": {0} }'.format(field) },
				],
				response_format={"type": "json"},
				stream=False,
			)
		except Exception as e:
			raise e

		return json.load(response.choices[0].message.content)
	
	def change_answer(self, field: str, ai_question: str, issues: str) -> Any:
		""" 
		Принимает сгенерированный вопрос, поле, и описание проблем с вопросом.
		Возвращает json с исправленным вопросом.
		"""
		
		try:
			response = self._client.chat.completions.create(
				model=self._model,
				messages=[
					{"role": "system", "content": str(self._change_answer_prompt)},
					{"role": "user", "content": '{ "field": {0}, "quetion": {1}, "issues": {2} }'.format(field, ai_question, issues) },
				],
				response_format={"type": "json"},
				stream=False,
			)
		except Exception as e:
			raise e

		return json.load(response.choices[0].message.content)


class AI_Validator:
	def __init__(self):

		self._ai_promt = """
		о ТЕБЕ:
		Ты эксперт по валидации даннных.
		На вход ты получаешь название поля и вопрос, который был сгенерирован для пользователя по названию поля.
		ТВОЯ ЗАДАЧА:
		1. Проверить, что вопрос соответствует названию поля.
		ПРАВИЛА:
		1. Ответ возврщай в формате JSON со следующей структурой.
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
		1. Проверить, что отве соответствует требованиям вопроса.
		ПРАВИЛА:
		1. Ответ возвращай в формате JSON со следующей структурой.
		ФОРМАТ ВХОДНЫХ ДАННЫХ:
		{
			"quetion":  "вопрос, сгенерированный для пользователя",
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
		

	def validate_ai_quetion(self, field: str, ai_question : str) -> Any:
		""" 
		Принимает название поля и сгенерированный вопрос.
		Возвращает json с результатами валидации вопроса."""
		try:
			response = self._client.chat.completions.create(
			model=self._model,
				messages=[
					{"role": "system", "content": str(self._ai_promt)},
					{"role": "user", "content": '{ "field": "{0}","quetion":"{1}"}'.format(field, ai_question) },
				],
				response_format={"type": "json"},
				stream=False
			)
		except Exception as e:
			raise e

		return json.load(response.choices[0].message.content)
	

	def validate_user_answer(self, ai_question: str, user_answer : str) -> Any:
		""" 
		Принимает сгенерированный вопрос и ответ пользователя.
		Возвращает json с результатами валидации ответа.
		"""
		try:
			response = self._client.chat.completions.create(
			model=self._model,
				messages=[
					{"role": "system", "content": str(self._user_promt)},
					{"role": "user", "content": '{ "quetion": "{0}", "answer" : "{1}"}'.format(ai_question, user_answer) },
				],
				response_format={"type": "json"},
				stream=False
			)
		except Exception as e:
			raise e

		return json.load(response.choices[0].message.content)
	