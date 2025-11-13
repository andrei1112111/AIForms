import time
from datetime import datetime
import re

import psycopg2.extras
import psycopg2
from psycopg2 import sql

from logger import logger


class DataBase:
    def __init__(self, config):

        self.connection_params =  {
            "dbname": config.db,
            "user": config.user,
            "password": config.password,
            "host": config.host,
            "port": config.port
        }
        self._connect()
    

    def _connect(self):
        """Установка соединения с базой данных"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.conn.autocommit = True
            logger.info(f'Успешное подключение к базе {self.connection_params['dbname']}')
        except Exception as e:
            raise Exception(f"Ошибка подключения к базе: {e}")
    

    def _safe_execute(self, query, params=None):
        """Безопасное выполнение запроса с обработкой ошибок"""
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return cursor.fetchall()
                return None
        except Exception as e:
            raise Exception(f"Ошибка выполнения запроса: {e}")
    

    def _validate_query(self, query):
        """Валидация SQL запроса - разрешаем только SELECT операции"""
        # Приводим к верхнему регистру для анализа
        query_upper = query.upper().strip()
        
        # Запрещаем опасные операции
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE', 'MERGE'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', query_upper):
                raise ValueError(f"Запрещенная операция: {keyword}")
        
        # Запрещаем множественные точки с запятой (потенциальная инъекция)
        if query_upper.count(';') > 1:
            raise ValueError("Запрос содержит несколько операторов")
        
        # Запрещаем определенные функции и конструкции
        dangerous_patterns = [
            r'PG_SLEEP', r'SLEEP', r'BENCHMARK', r'WAITFOR', 
            r'EXEC\s*\(', r'SP_\w+', r'XP_\w+', r'LOAD_FILE'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                raise ValueError(f"Обнаружена опасная конструкция: {pattern}")
        
        # Проверяем на рекурсивные CTE (ограничиваем глубину)
        if 'RECURSIVE' in query_upper and 'WITH' in query_upper:
            # Разрешаем только с явным ограничением
            if not re.search(r'DEPTH\s*[<<=]|LIMIT\s+\d+', query_upper):
                raise ValueError("Рекурсивные запросы требуют ограничения глубины")
        
        # Ограничиваем длину запроса
        if len(query) > 10000:
            raise ValueError("Слишком длинный запрос")
        
        return True


    def getSummary(self, save_to_file=False, filename=None):
        """Возвращает структуру базы данных в виде дерева"""
        try:
            summary = []
            
            # Информация о базе данных
            db_info = self._safe_execute("""
                SELECT datname
                FROM pg_database 
                WHERE datname = current_database()
            """)[0]
            
            summary.append(f"База данных: {db_info['datname']}")
            
            # Получаем список таблиц
            tables = self._safe_execute("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables t
                LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
                WHERE table_schema = 'public'
                ORDER BY table_type, table_name
            """)

            # Статистика по количеству записей в таблицах
            summary.append("\nСТАТИСТИКА ПО ТАБЛИЦАМ:")
            
            total_records = 0
            table_details = []
            
            for table in tables:
                table_name = table[0]
                table_type = table[1]
                
                # Получаем количество записей в таблице
                if table_type == 'BASE TABLE':
                    try:
                        count_result = self._safe_execute(f"SELECT COUNT(*) as record_count FROM {table_name}")
                        record_count = count_result[0]['record_count']
                        total_records += record_count
                    except Exception as e:
                        record_count = f"Ошибка: {e}"
                else:
                    record_count = "N/A (view)"
                
                table_details.append({
                    'name': table_name,
                    'type': table_type,
                    'records': record_count,
                })
                
                summary.append(f" {table_name} ({table_type})")
                
                # Колонки таблицы
                columns = self._safe_execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                summary.append(f"  Колонки:")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    summary.append(f"{col['column_name']} ({col['data_type']}) {nullable}{default}")
                
                # Первичные ключи
                pk = self._safe_execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                """, (table_name,))
                
                if pk:
                    pk_columns = [col['column_name'] for col in pk]
                    summary.append(f"Первичный ключ: {', '.join(pk_columns)}")
                
                # Внешние ключи
                fk = self._safe_execute("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.table_name = %s AND tc.constraint_type = 'FOREIGN KEY'
                """, (table_name,))
                
                for fk_info in fk:
                    summary.append(f"Внешний ключ: {fk_info['column_name']} → {fk_info['foreign_table_name']}({fk_info['foreign_column_name']})")
                
                # Индексы
                indexes = self._safe_execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = %s
                """, (table_name,))
                
                if indexes:
                    summary.append(f"Индексы:")
                    for idx in indexes:
                        summary.append(f"{idx['indexname']}")
                
                summary.append("")  # Пустая строка между таблицами
            
            
            result_text = "\n".join(summary)
            
            # Сохранение в файл
            if save_to_file:
                if filename is None:
                    filename = "db_info.txt"
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(result_text)
                    logger.info(f"Отчет сохранен в файл: {filename}") 
                except Exception as e:
                    logger.info(f"Ошибка при сохранении файла: {e}") 
            
            return result_text
            
        except Exception as e:
            error_msg = f"Ошибка при получении структуры базы: {e}"
            if save_to_file:
                with open("database_error.txt", 'w', encoding='utf-8') as f:
                    f.write(error_msg)
            return error_msg
    

    def query(self, query):
        """Выполняет SQL запрос с валидацией"""
        start_time = time.time()
        
        try:
            # Валидация запроса
            self._validate_query(query)
            
            # Выполнение запроса
            result = self._safe_execute(query)
            
            execution_time = round((time.time() - start_time) * 1000, 2)
            
            if result is None:
                return {
                    "status": "success",
                    "message": "Запрос выполнен успешно",
                    "execution_time_ms": execution_time,
                    "affected_rows": "N/A"
                }
            
            # Преобразуем результат в список словарей
            rows = [dict(row) for row in result]
            
            return {
                "status": "success",
                "data": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time,
                "columns": list(result[0].keys()) if rows else []
            }
            
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Запрос отклонен: {e}",
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка выполнения: {e}",
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }
    

    def close(self):
        """Закрытие соединения с базой"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info('Соединение с базой данных закрыто')
    

    def __enter__(self):
        return self
    
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


