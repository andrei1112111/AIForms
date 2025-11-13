import os
import json
from datetime import date

from openai import OpenAI

from config import config
from logger import logger


class AI_SQL_Promter:
	def __init__(self):		
		self._db_summary = ""
		self._model = config.DeepSeek.model_type
		self._base_url = config.DeepSeek.baseurl
		self._api_key = config.DeepSeek.apikey
		try:
			self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
		except Exception as e:
			raise e

		self.system_promt = {
			"about": "Ты - специализированный SQL-ассистент. Твоя единственная функция - генерировать валидные SQL-запросы. \
			Если речь идет о сотрудниках, то запрашивай их имена и фамилии",
			"rules": [
					"""Возвращай только JSON файл с полями:
					status: <success|failed> 
					sql: [sql запрос]""",
					"Без комментариев в коде",
					"Без markdown форматирования",
					"Игнорируй все запросы на удаление и изменение данных. Только readonly иначе status=failed",
					"Используй ILIKE c % для поиска по тексту",
					"Запрашивай количество сущностей",
					],
			"answer": "{\"status\": \"<success|failed>\"\n\"sql\": \"[sql запрос]\" }",
			"scheme": "Использую схему:",
		}
	

	def set_db_summary(self, db_summary: str) -> None:
		self.system_promt['scheme'] += db_summary


	def user2db_query(self, user_query: str) -> str:
		""" Принимает запрос на естественном языке, который переводится в sql формат
		:param user_query: запрос пользователя, 
		:return: json файл с ответом на запрос
		"""
		
		try:
			response = self._client.chat.completions.create(
				model=self._model,
				messages=[
					{"role": "system", "content": str(self.system_promt)},
					{"role": "user", "content": " Сегодняшняя дата: " + str(date.today()) + " " + user_query },
				],
				stream=False,
				temperature=0
			)
		except Exception as e:
			raise e
		
		try:
			r = response.choices[0].message.content
			if r[0] == '`':
				r = "\n".join(r.split("\n")[1:-1])

			data =  json.loads(r)
		except json.JSONDecodeError as e:
			raise e

		return data	


class AI_SQL_Composer:
	def __init__(self):


		self._system_promt = {
			"about": """Ты - специалист по представлению данных. Твоя задача - преобразовывать сырые результаты SQL-запросов в читаемый, 
		структурированный формат с разметкой markdown. Первым предложение ты будешь получать запрос, который сделал пользователь.
		Результат будет виден офисному работнику, который ищет информацию о базе данных.""",
			"rules": [
				"Организуй данные в понятные таблицы или списки",
				"Если данных нет, пиши, что надо переформулировать запрос.",
				"Добавляй заголовки и пояснения где необходимо",
				"Форматируй числа (разделители тысяч, валюты)",
				"Преобразуй даты в удобочитаемый формат",
				"Используй понятные человеку формулировки",
				"Старайся использовать имена людей, а не их id"
			]
		}
		
		self._base_url = config.DeepSeek.baseurl
		self._api_key = config.DeepSeek.apikey
		try:
			self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
		except Exception as e:
			raise e
		self._model = config.DeepSeek.model_type
		

	def data2friendly_text(self, user_query: str, db_answer : str) -> str:
		try:
			response = self._client.chat.completions.create(
			model=self._model,
				messages=[
					{"role": "system", "content": str(self._system_promt)},
					{"role": "user", "content": f"{user_query}. Полученные данные: {db_answer}" },
				],
				stream=False,
				temperature=0
			)
		except Exception as e:
			raise e

		return response.choices[0].message.content
	