from .models import AI_SQL_Promter, AI_SQL_Composer
"""
создает запрос к бд и обрабатывает ответ от бд


"""

# class AI_SQL_Prompter():
"""
    init(название модели openai / deepseak и тп, саммари по бд)
    user2bd_query(user_query) -> sql_query
"""
# system prompt ты генератор sql запросов

# class AI_Composer():
"""
    init(название модели openai / deepseak и тп, саммари по бд)
    database_data2userfrandly_text(user_query, database_data) -> text на естественно языке
"""
# system prompt ты чатбот


# sql_prompt_generator = AI_SQL_Prompter(config_data) 
# ai_composer = AI_Composer(config_data)

sql_prompt_generator = AI_SQL_Promter()
ai_composer = AI_SQL_Composer()



__all__ = [
    "sql_prompt_generator",
    "ai_composer"
]
