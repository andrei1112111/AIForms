from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import requests

from model import predict
from config import config
from db.entity import User, Form
from db.repository import userRepository, formRepository

app = Flask(__name__)
app.template_folder = "frontend/templates"
app.secret_key = "your-secret-key"

HOST = "0.0.0.0"
PORT = 8080

# Настройки Google OAuth2
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # разрешаем HTTP для теста
GOOGLE_CLIENT_ID = config.GoogleAPIs.google_client_id
GOOGLE_CLIENT_SECRET = config.GoogleAPIs.google_client_secret
REDIRECT_URI = config.GoogleAPIs.redirect_url

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/drive.file",  # для создания файлов
    "https://www.googleapis.com/auth/spreadsheets"  # для Google Sheets
]

@app.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:  # бросаем юзера в авторизацию чрез google
        return render_template("login.html")

    user = userRepository.get_by_id(user_id)
    if not user:
        session.clear()
        return render_template("login.html")

    return render_template("dashboard.html", email=user.email)


# авторизация через google
@app.route("/login")
def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    session["state"] = state
    return redirect(authorization_url)

# callback для авторизации через google
@app.route("/callback")
def callback():
    state = session.get("state")
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"},
    ).json()

    # Сохраняем пользователя в БД
    user = userRepository.get_by_email(userinfo["email"])
    if not user:
        user = User(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_url=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=",".join(credentials.scopes),
            email=userinfo["email"]
        )
        userRepository.add(user)
    else:
        # Обновляем токены существующего пользователя
        user.token = credentials.token
        user.refresh_token = credentials.refresh_token
        user.token_url = credentials.token_uri
        user.client_id = credentials.client_id
        user.scopes = ",".join(credentials.scopes)
        userRepository.update_user(user)

    session["user_id"] = user.id
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def get_user_credentials(user_id):
    user = userRepository.get_by_id(user_id)
    if not user:
        return None

    return Credentials(
        token=user.token,
        refresh_token=user.refresh_token,
        token_uri=user.token_url,
        client_id=user.client_id,
        client_secret=user.client_secret,
        scopes=user.scopes.split(",")
    )


def create_user_sheet(user_id, columns, title="AI Form Responses", description="не указано"):
    """
    Создает таблицу с заданными колонками.
    Возвращает URL и ID таблицы.
    """
    creds = get_user_credentials(user_id)
    if not creds:
        return None

    service = build("sheets", "v4", credentials=creds)

    # запрос на создание таблички
    spreadsheet = service.spreadsheets().create(
        body={"properties": {"title": title}},
        fields="spreadsheetId"
    ).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]
    print(columns)

    # создаем шапку таблицы
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [[i["name"] for i in columns]]}
    ).execute()

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    # Сохраняем форму в БД
    chat_id = len(formRepository.get_forms_by_user_id(user_id)) + 1
    public_link = f"http://{HOST}:{PORT}/chat/{user_id}/{chat_id}"

    form = Form(
        columns=columns,
        title=title,
        url=url,
        description=description,
        chat_link=public_link,
        creator_id=user_id
    )
    formRepository.add(form)

    return {
        "id": spreadsheet_id,
        "url": url,
        "title": title,
        "columns": columns,
        "description": description,
        "chat_id": chat_id,
        "public_link": public_link
    }


def update_user_sheet(user_id, spreadsheet_id, values_dict, expected_columns):
    """
    Добавляет строку в таблицу по словарю: {column: value}.
    expected_columns: порядок колонок
    """
    creds = get_user_credentials(user_id)
    if not creds:
        return {"error": "User not found"}

    service = build("sheets", "v4", credentials=creds)

    if expected_columns:
        columns = expected_columns
        values = [values_dict.get(col, "") for col in columns]  # если значение отсутствует, ставим пустую строку
    else:
        columns = list(values_dict.keys())
        values = list(values_dict.values())

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [values]}
    ).execute()

    return {"status": "ok", "inserted": dict(zip(columns, values))}


@app.route("/create_form")
def create_form():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("create_form.html")


@app.route("/edit_forms")
def edit_forms():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("edit_forms.html")


@app.route("/chat/<creator_user_id>/<chat_id>")
def chat_interface(creator_user_id, chat_id):
    """Страница чата для конкретной формы"""
    if "user_id" not in session:
        return redirect(url_for("index"))

    user_id = session["user_id"]
    form = formRepository.get_by_chat_link(f"http://{HOST}:{PORT}/chat/{creator_user_id}/{chat_id}")

    # Находим форму по chat_id (в данном случае используем порядковый номер)
    if not form:
        return "Чат не найден", 404

    return render_template("chat.html",
                           form_title=form.title,
                           form_description=form.description,
                           chat_id=chat_id,
                           creator_user_id=creator_user_id
                           )


# метод для создания формы
@app.route("/api/create_sheet", methods=["POST"])
def api_create_sheet():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authorized"}), 401

    data = request.json
    columns = data.get("columns", [])
    title = data.get("title", "AI Form Responses")
    description = data.get("description", "не указано")

    result = create_user_sheet(user_id, columns, title, description)
    if not result:
        return jsonify({"error": "Failed to create sheet"}), 500

    return jsonify(result)


# метод для общения с пользователем при заполнении формы в виде чата
@app.route("/api/chat/<creator_user_id>/<chat_id>/send", methods=["POST"])
def api_chat_send(creator_user_id, chat_id):
    """Обработка сообщений в чате с ИИ"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authorized"}), 401

    data = request.json
    user_response = data.get("user_response", "")
    previous_question = data.get("previous_question", "")
    current_data = data.get("current_data", {})

    # Получаем формы пользователя и находим нужную по chat_id
    form = formRepository.get_by_chat_link(f"http://{HOST}:{PORT}/chat/{creator_user_id}/{chat_id}")
    if not form:
        return jsonify({"error": "Form not found"}), 404

    if current_data == {}:
        current_data = {i['name']: "" for i in form.columns}

    # Подготавливаем запрос для ИИ
    ai_request = {
        "previous_question": previous_question,
        "user_response": user_response,
		"behavior": form.description,
        "table_description": {i['name']: i['desc'] for i in form.columns},
        "current_data": current_data
    }

    # запрос в chat модельку
    ai_response = predict(str(ai_request))

    # парсим ответ модельки
    question = ai_response.get("question", "")
    data = ai_response.get("data", {})

    if question == "success":
        update_user_sheet(creator_user_id, form.url.split("/d/")[1].split("/")[0], data, [i['name'] for i in form.columns])

    return jsonify({"question": question, "data": data})


# апдейт состояния таблицы
@app.route("/api/update_sheet", methods=["POST"])
def api_update_sheet():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authorized"}), 401

    data = request.json
    spreadsheet_id = data.get("spreadsheet_id")
    if not spreadsheet_id:
        return jsonify({"error": "No spreadsheet ID provided"}), 400

    result = update_user_sheet(user_id, spreadsheet_id, data, None)
    return jsonify(result)


# список таблиц пользователя
@app.route("/api/list_sheets")
def api_list_sheets():
    """Возвращает список таблиц пользователя"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authorized"}), 401

    forms = formRepository.get_forms_by_user_id(user_id)

    # Преобразуем формы в формат для фронтенда
    sheets_list = []
    for i, form in enumerate(forms, 1):
        sheets_list.append({
            "id": form.id,
            "url": form.url,
            "title": form.title,
            "columns": [f"{c['name']}: {c['desc']}" for c in form.columns],
            "description": form.description,
            "chat_id": i,
            "public_link": form.chat_link
        })

    return jsonify(sheets_list)


# удаление формочки
@app.route("/api/delete_form/<int:form_id>", methods=["POST"])
def api_delete_form(form_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authorized"}), 401

    # Получаем форму
    form = formRepository.get_by_id(form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    # Проверка, что форма принадлежит пользователю
    if form.creator_id != user_id:
        return jsonify({"error": "You don't have permission to delete this form"}), 403

    formRepository.delete(form)

    # Удаляем Google Sheet
    creds = get_user_credentials(user_id)
    if creds:
        service = build("sheets", "v4", credentials=creds)
        try:
            service.spreadsheets().delete(spreadsheetId=form.url.split("/d/")[1].split("/")[0]).execute()
        except Exception as e:
            pass

    return jsonify({"status": "ok", "message": "Form deleted"})


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
