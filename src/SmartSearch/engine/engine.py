import json
from logger import logger


class SearchEngine:
    def __init__(self, sql_generator, composer, database) -> None:
        self.sql_generator = sql_generator
        self.composer = composer
        self.database = database
    

    def request2sql(self, request : str, userinfo : str) -> dict:
        """
        Поиск данных в базе по SQL запросу от модели sql_generator
        request - запрос пользователя, который будет виден sql_generator
        userinfo - Информация о пользователе, которая будет видна sql_generator
        """
        prompt = f"Пользователь, который спрашивает: {userinfo}. Запрос пользователя: {request}"
        
        ans = self.sql_generator.user2db_query(prompt)
        logger.debug(str(ans)[:1000])
        if ans["status"] == "failed":
            if userinfo["user_id"] == None or not not userinfo["user_id"].isdigit():
                return {"status": "failed", "text": "Не удалось сделать sql запрос. Возможно не хватает информации о пользователе."}

            return {"status": "failed", "text": "Не удалось сделать sql запрос"}

        return {"status": "success", "text": ans["sql"]}

    def sql2data(self, query : str) -> dict:
        """
        Обращение к database по SQL запросу с получением ответа
        :param query: SQL запрос к базе данных, ответ на который вернется на выходе функции
        """
        data = self.database.query(query)
        logger.debug(str(data)[:1000])
        if data["status"] != "success":
            return {"status": "failed", "text": "Не удалось выполнить sql запрос"}
    
        return {"status": "success", "text": data["data"]}


    def request_and_data2response(self, request : str, data : str) -> str:
        """
        Преобразование ответа от database в читаемый текст, используя composer
        :param request: Запрос пользователя
        :param data: Информация из базы данных
        """
        reply = self.composer.data2friendly_text(request, data)
        reply = reply.replace("```", "")
        logger.debug(str(reply)[:1000])
        return reply
      
    def validate_user(self, company, userinfo):
        """
        Производит валидацию пользователя через базу данных
        :param company: Название компании пользователя
        :param userinfo: Информация о пользователе
        """
        prompt_search = f"Найди user_id, department_id пользователя, если есть информация о пользователе: {userinfo} и его department: {company}"
        prompt_search_result2json = """
            Найди id пользователя и выведи его в формате
            {'status': 'success'или'failed', 'user_id': user_id,'department_id': 'department_id'}.
            Не добавляй никакого текста до или после JSON. Не используй markdown-разметку, блоки кода или обратные кавычки.
            Данные: """

        ans = self.sql_generator.user2db_query(prompt_search)
        logger.debug(ans)
        if ans["status"] != "success":
            return {"status": "failed", "text": "Не удалось сделать sql запрос"}

        query = ans["sql"]
        data = self.database.query(query)
        logger.debug(str(data)[:1000])

        if data["status"] != "success":
            return {"status": "failed", "text": "Не удалось выполнить sql запрос"}
        
        self.sql_generator.system_promt['the_user_who_asks'] = userinfo
        
        info = data["data"]
        logger.debug(str(info)[:1000])

        if info == []:
            return {"status": "failed", "text": "Данные не найдены"}
        
        reply = self.composer.data2friendly_text(prompt_search_result2json, info)

        if reply[0] == "`":
            reply = '\n'.join(reply.split("\n")[1:-1])

        logger.debug(str(reply)[:1000])

        reply = json.loads(reply)

        return reply
        
