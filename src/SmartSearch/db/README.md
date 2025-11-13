# Класс DataBase для работы с PostgreSQL

Этот модуль реализует безопасный и удобный способ работы с PostgreSQL.  
Он включает автоматическое подключение, безопасное выполнение запросов, защиту от SQL-инъекций, а также генерацию отчёта о структуре базы данных.

## Про генерацию отчета
При инициализации модуля автоматически создается отчет о бд для дальнейшей загрузки в системный промпт модели выполняющей создание sql.
формат отчета подобный:
```
База данных: company_employees_db

СТАТИСТИКА ПО ТАБЛИЦАМ:
 companies (BASE TABLE)
  Колонки:
id (integer) NOT NULL DEFAULT nextval('companies_id_seq'::regclass)
name (character varying) NOT NULL
legal_name (character varying) NULL
inn (character varying) NULL
...
Первичный ключ: id
Индексы:
companies_pkey
companies_name_key
idx_companies_name
idx_companies_is_active

 departments (BASE TABLE)
  Колонки:
...
```


## Пример использования
``` python
from dataclasses import dataclass
from database import DataBase  # замените на имя файла, где лежит твой код

# 1. Определяем конфиг для подключения
@dataclass
class Config:
    db: str = "my_database"
    user: str = "postgres"
    password: str = "my_password"
    host: str = "localhost"
    port: int = 5432

# 2. Используем контекстный менеджер, чтобы соединение закрылось автоматически
if __name__ == "__main__":
    config = Config()

    with DataBase(config) as db:
        # 3. Получаем структуру БД и печатаем в консоль
        print("=== Структура базы ===")
        summary_text = db.getSummary(save_to_file=True)
        print(summary_text)

        # 4. Выполняем безопасный SELECT-запрос
        result = db.query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        
        if result["status"] == "success":
            print(f"Запрос выполнен успешно за {result['execution_time_ms']} мс")
            print(f"Найдено строк: {result['row_count']}")
            for row in result["data"]:
                print(row)
        else:
            print(f"Ошибка запроса: {result['message']}")

    # После выхода из блока with соединение автоматически закрывается
```

## **[На главную](../../../README.md)** 
