FROM python:3.11-slim

# Устанавливаем зависимости
COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Копируем .env из корня проекта
COPY .env /.env

# Копируем всю папку src внутрь контейнера
COPY src/ /src

# Запускаем приложение
CMD ["ls"]
CMD ["python", "src/app.py"]
