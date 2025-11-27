# Database - AIForms

Модуль для работы с базой данных PostgreSQL. Содержит логику подключения, ORM модели (Entity) и слой доступа к данным (Repository).

## Структура папки

```
db/
├── README.md                    # Этот файл
├── db.py                        # Инициализация движка SQLAlchemy
├── connect_db.py               # Функции подключения и отключения от БД
├── session.py                  # Создание сессий SQLAlchemy
├── debug_db.py                 # Утилиты для отладки строк подключения
├── init.sql                    # SQL скрипт инициализации БД
├── Dockerfile                  # Docker контейнер для PostgreSQL
├── docker-compose.yaml         # Конфигурация Docker Compose
├── entity/                     # ORM модели (Entities)
│   ├── base_entity.py          # Базовая конфигурация для всех моделей
│   ├── form_entity.py          # Модель формы
│   └── user_entity.py          # Модель пользователя
└── repository/                 # Data Access Layer (Repository)
    ├── form_repository.py      # Репозиторий для работы с формами
    └── user_repository.py      # Репозиторий для работы с пользователями
```

## Компоненты

### db.py
**Назначение:** Создание и инициализация SQLAlchemy engine

**Функции:**
- Создает подключение к PostgreSQL (`postgresql+psycopg2://user_name:user_password@host:port/aiforms`)
- Настройка пула соединений (pool_size=5, max_overflow=10)
- Проверка доступности БД при запуске
- Вывод статуса подключения

```python
engine = create_engine(
    "postgresql+psycopg2://user_name:user_password@host:port/aiforms",
    pool_size=5,
    max_overflow=10
)
```

### connect_db.py
**Назначение:** Управление жизненным циклом подключения к БД

**Функции:**
- `connect_db()` - подключение и создание всех таблиц (если не существуют)
- `disconnect_db()` - закрытие соединения с БД

**Использование:**
```python
from db.connect_db import connect_db, disconnect_db

connect_db()      # Подключиться и создать таблицы
# Работа с БД
disconnect_db()   # Отключиться
```

### session.py
**Назначение:** Создание сессий для работы с ORM

**Экспортирует:**
- `Session` - фабрика сессий SQLAlchemy

**Использование:**
```python
from db.session import Session

session = Session()
# Работа с сессией
session.close()
```

### Entity (ORM модели)

#### base_entity.py
- `Base` - базовый класс для всех ORM моделей, создается через `declarative_base()`

#### form_entity.py
**Модель:** `Form` (таблица `forms`)

**Поля:**
- `id` - PRIMARY KEY (INTEGER)
- `columns` - JSON колонки формы (JSONB)
- `title` - название формы (TEXT)
- `url` - ссылка на Google Sheets (TEXT)
- `description` - описание формы (TEXT)
- `chat_link` - ссылка на чат для заполнения (TEXT)
- `created_at` - дата создания (DATETIME, автоматически текущее время)
- `creator_id` - ID создателя формы (INTEGER)

#### user_entity.py
**Модель:** `User` (таблица `users`)

**Поля:**
- `id` - PRIMARY KEY (INTEGER)
- `token` - OAuth токен (TEXT)
- `refresh_token` - токен обновления (TEXT)
- `token_url` - URL для получения токена (TEXT)
- `client_id` - Google Client ID (TEXT)
- `client_secret` - Google Client Secret (TEXT)
- `scopes` - права доступа (TEXT)
- `email` - email пользователя (TEXT)

### Repository (Data Access Layer)

#### form_repository.py
**Класс:** `FormRepository`

**Методы:**
- `add(form)` - добавить новую форму
- `get_by_id(id)` - получить форму по ID
- `get_forms_by_user_id(id)` - получить все формы конкретного пользователя
- `get_by_chat_link(chat_link)` - получить форму по ссылке чата
- `get_by_title(title)` - получить форму по названию
- `get_all()` - получить все формы
- `delete(form)` - удалить форму

**Использование:**
```python
from db.session import Session
from db.repository.form_repository import FormRepository
from db.entity.form_entity import Form

session = Session()
repo = FormRepository(session)

# Добавить форму
form = Form(title="Анкета", columns=[...], url="...", description="...", chat_link="...", creator_id=1)
repo.add(form)

# Получить форму
form = repo.get_by_id(1)

# Получить все формы пользователя
forms = repo.get_forms_by_user_id(1)

# Удалить форму
repo.delete(form)
```

#### user_repository.py
**Класс:** `UserRepository`

**Методы:**
- `add(user)` - добавить нового пользователя
- `get_by_id(id)` - получить пользователя по ID
- `get_by_email(email)` - получить пользователя по email
- `get_all()` - получить всех пользователей
- `update_user(user)` - обновить данные пользователя

**Использование:**
```python
from db.session import Session
from db.repository.user_repository import UserRepository
from db.entity.user_entity import User

session = Session()
repo = UserRepository(session)

# Добавить пользователя
user = User(email="user@example.com", token="...", refresh_token="...", ...)
repo.add(user)

# Получить пользователя
user = repo.get_by_email("user@example.com")

# Обновить пользователя
user.token = "new_token"
repo.update_user(user)
```

## Инициализация БД

### init.sql
SQL скрипт для инициализации БД. Создает две таблицы:

**Таблица `forms`:**
```sql
CREATE TABLE forms (
    id SERIAL PRIMARY KEY,
    columns JSONB NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL,
    chat_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    creator_id INTEGER NOT NULL
);
```

**Таблица `users`:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_url TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    scopes TEXT NOT NULL,
    email TEXT NOT NULL
);
```

## Docker

### Dockerfile
Контейнер PostgreSQL с предустановками для проекта.

### docker-compose.yaml
Конфигурация для развертывания БД через Docker Compose.

**Запуск БД:**
```bash
docker-compose up -d
```

**Остановка БД:**
```bash
docker-compose down
```

## Использование

### Базовый пример
```python
from db.connect_db import connect_db
from db.session import Session
from db.repository.form_repository import FormRepository
from db.entity.form_entity import Form

# Подключиться к БД
connect_db()

# Создать сессию
session = Session()

# Создать репозиторий
form_repo = FormRepository(session)

# Добавить форму
new_form = Form(
    title="Опрос",
    columns=[{"name": "Имя", "desc": "Введите имя"}],
    url="https://sheets.google.com/...",
    description="Опрос сотрудников",
    chat_link="http://localhost:5000/chat/...",
    creator_id=1
)
form_repo.add(new_form)

# Получить форму
form = form_repo.get_by_id(1)
print(form.title)

# Получить все формы пользователя
user_forms = form_repo.get_forms_by_user_id(1)

session.close()
```

## Конфигурация

Параметры подключения указаны в `db.py`:
- **Хост:** localhost
- **Порт:** 5432
- **БД:** aiforms
- **Пользователь:** postgres
- **Пароль:** 43720

Для изменения параметров отредактируйте строку подключения в `db.py`.

## Утилиты

### debug_db.py
Содержит функцию `debug_string()` для отладки строк подключения. Проверяет все компоненты строки подключения и выводит информацию о них.

**Использование:**
```bash
python debug_db.py
```

[НАЗАД](../../README.md) 
