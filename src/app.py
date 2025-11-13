from SmartSearch import engine
from flask import Flask, render_template, request, jsonify, make_response, send_file, Response
from datetime import datetime, timedelta
import json
import io
import time
from urllib.parse import quote


import logging
# Отключаем логи Flask и Werkzeug
logging.getLogger("flask").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)

# Отключаем логи httpx, urllib3
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# httpcore
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

# иногда "trace" уходит в отдельный логгер
logging.getLogger("httpx.trace").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.trace").setLevel(logging.CRITICAL)


app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)

class DateTimeEncoder(json.JSONEncoder):
    """Кастомный энкодер для сериализации datetime объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Глобальная переменная для хранения временных данных (в продакшене используйте Redis или БД)
temp_data_store = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    data = request.get_json() or {}
    company = data.get('company', '').strip()
    name = data.get('username', '').strip()

    info = engine.validate_user(company, name)
    
    if info["status"] != "success":
        return jsonify({'ok': False, 'error': 'Неверные данные'}), 400

    resp = make_response(
        jsonify({
            'ok': True,
            'user_id': info["user_id"],
            'department_id': info["department_id"],
            'name': name,
            'company': company
        })
    )
    
    max_age = 60 * 60 * 24 * 30
    expires = datetime.utcnow() + timedelta(seconds=max_age)

    resp.set_cookie('user_id', str(info["user_id"]), max_age=max_age, expires=expires, httponly=False, samesite='Lax')
    resp.set_cookie('department_id', str(info["department_id"]), max_age=max_age, expires=expires, httponly=False, samesite='Lax')
    resp.set_cookie('name', quote(name, safe=''), max_age=max_age, expires=expires, httponly=False, samesite='Lax')
    resp.set_cookie('company', quote(company, safe=''), max_age=max_age, expires=expires, httponly=False, samesite='Lax')

    return resp

@app.route('/download-data')
def download_data():
    data_id = request.args.get('data_id', '')
    if not data_id or data_id not in temp_data_store:
        return jsonify({'error': 'Нет данных для скачивания'}), 400
    
    data_content = temp_data_store[data_id]['data']

    # Создаем файл в памяти
    data_io = io.BytesIO()
    data_io.write(json.dumps(data_content, ensure_ascii=False, indent=2, cls=DateTimeEncoder).encode('utf-8'))
    data_io.seek(0)
    
    filename = f"search_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Очищаем временные данные после скачивания
    del temp_data_store[data_id]
    
    return send_file(
        data_io,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

@app.route('/generate-with-limited-data', methods=['POST'])
def generate_with_limited_data():
    data = request.get_json() or {}
    data_id = data.get('data_id', '')
    
    if not data_id or data_id not in temp_data_store:
        return jsonify({'ok': False, 'error': 'Данные не найдены'}), 400
    
    stored_data = temp_data_store[data_id]
    query = stored_data['query']
    full_data = stored_data['data']
    
    # Очищаем временные данные
    del temp_data_store[data_id]
    
    # Обрезаем данные до 4000 символов
    # limited_data = str(full_data)[:4000]
    
    # Генерируем ответ с ограниченными данными
    response = engine.request_and_data2response(query, full_data)
    
    return jsonify({
        'ok': True, 
        'reply': f"**Внимание:** Модель могла учесть не все данные.\n\n{response}",
        'stage': ''
    })

def generate_progress(query, user_info):
    """Генератор для отправки прогресса через SSE"""
    
    def send_progress(stage, message="", data=None, is_final=False):
        progress_data = {
            'stage': stage,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data:
            progress_data['data'] = data
        if is_final:
            progress_data['final'] = True
        
        return f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
    
    try:
        # Стадия 1: Формируем SQL запрос
        yield send_progress('(1/3) → Формируем SQL запрос', 'Анализируем ваш запрос...')
        time.sleep(0.5)
        
        sql = engine.request2sql(query, user_info)
        if sql.get("status") != "success":
            yield send_progress('', sql.get("text", "Ошибка формирования SQL"), is_final=True)
            return
        
        yield send_progress('(2/3) → Ищем в базе данных', 'Выполняем поиск по базе...')
        time.sleep(0.5)
        
        # Стадия 2: Поиск по базе данных
        data_result = engine.sql2data(sql.get("text", ""))
        if data_result.get("status") != "success":
            yield send_progress('', data_result.get("text", "Ошибка выполнения запроса"), is_final=True)
            return
        
        data_text = data_result.get("text", "")
        data_size = len(str(data_text))
        
        yield send_progress('(2/3) → Данные получены', f'Найдено {data_size} символов данных')
        time.sleep(0.5)
        
        # Проверяем размер данных
        if data_size > 4000:
            # Сохраняем данные во временное хранилище
            data_id = f"data_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(query)}"
            temp_data_store[data_id] = {
                'query': query,
                'data': data_text,
                'timestamp': datetime.now()
            }
            
            # Очищаем старые данные (больше 1 часа)
            current_time = datetime.now()
            for key in list(temp_data_store.keys()):
                if (current_time - temp_data_store[key]['timestamp']).total_seconds() > 3600:
                    del temp_data_store[key]
            
            yield send_progress(
                '', 
                f'Объем данных ({data_size} символов) превышает лимит',
                {
                    'large_data': True,
                    'data_id': data_id,
                    'data_size': data_size,
                    'data_preview': str(data_text)[:1000] + "..." if data_size > 1000 else str(data_text)
                },
                is_final=True
            )
            return
        
        # Стадия 3: Генерация ответа
        yield send_progress('(3/3) → Генерируем ответ', 'Обрабатываем данные и формируем ответ...')
        time.sleep(1)
        
        response = engine.request_and_data2response(query, data_text)
        
        yield send_progress(
            '', 
            '',
            {
                'reply': response,
                'large_data': False
            },
            is_final=True
        )
        
    except Exception as e:
        yield send_progress('Ошибка', f'Произошла ошибка: {str(e)}', is_final=True)

@app.route('/search-stream')
def search_stream():
    """SSE endpoint для потоковой передачи прогресса"""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Пустой запрос'}), 400
    
    user_info = {
        'user_id': request.cookies.get('user_id'),
        'department_id': request.cookies.get('department_id'),
        'name': request.cookies.get('name'),
        'company': request.cookies.get('company')
    }
    
    return Response(
        generate_progress(query, user_info),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
