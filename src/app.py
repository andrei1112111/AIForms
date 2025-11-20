from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import requests

app = Flask(__name__)
app.template_folder = "frontend/templates"
app.secret_key = "your-secret-key"

# Настройки Google OAuth2
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # разрешаем HTTP для теста
GOOGLE_CLIENT_ID = "624387588725-kljja5hh0d2jqb59nggni480m4p55ovv.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "http://127.0.0.1:5000/callback"

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/drive.file",  # для создания файлов
    "https://www.googleapis.com/auth/spreadsheets"  # для Google Sheets
]


# ======================
# OAuth2 авторизация
# ======================
@app.route("/")
def index():
    if "credentials" not in session:
        return render_template("login.html")
    return render_template("dashboard.html", email=session["credentials"].get("email"))


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


@app.route("/callback")
def callback():
    state = session["state"]
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

    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "email": userinfo["email"],
    }

    # Инициализируем список таблиц для пользователя
    if "user_sheets" not in session:
        session["user_sheets"] = []

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ======================
# Работа с Google Sheets
# ======================
def get_user_credentials():
    creds_info = session.get("credentials")
    if not creds_info:
        return None
    return Credentials(
        token=creds_info["token"],
        refresh_token=creds_info["refresh_token"],
        token_uri=creds_info["token_uri"],
        client_id=creds_info["client_id"],
        client_secret=creds_info["client_secret"],
        scopes=creds_info["scopes"]
    )


def create_user_sheet(columns, title="AI Form Responses", description="не указано"):
    """
    Создает таблицу с заданными колонками.
    Возвращает URL и ID таблицы.
    """
    creds = get_user_credentials()
    service = build("sheets", "v4", credentials=creds)

    spreadsheet = service.spreadsheets().create(
        body={"properties": {"title": title}},
        fields="spreadsheetId"
    ).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]

    # создаем шапку таблицы
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [columns]}
    ).execute()

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return {"id": spreadsheet_id,
            "url": url,
            "title": title,
            "columns": columns,
            "description": description,
            "chat_id": 1,
            "public_link": f"http://127.0.0.1:5000/chat/{1}"}


def update_user_sheet(spreadsheet_id, values_dict):
    """
    Добавляет строку в таблицу по словарю: {column: value}.
    """
    creds = get_user_credentials()
    service = build("sheets", "v4", credentials=creds)

    columns = list(values_dict.keys())
    values = list(values_dict.values())

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [values]}
    ).execute()

    return {"status": "ok", "inserted": dict(zip(columns, values))}


# ======================
# REST API для фронтенда
# ======================

@app.route("/create_form")
def create_form():
    if "credentials" not in session:
        return redirect(url_for("index"))
    return render_template("create_form.html")


@app.route("/edit_forms")
def edit_forms():
    if "credentials" not in session:
        return redirect(url_for("index"))
    return render_template("edit_forms.html")


@app.route("/chat/<chat_id>")
def chat_interface(chat_id):
    """Страница чата для конкретной формы"""
    if "credentials" not in session:
        return redirect(url_for("index"))

    form_data = "это формачка"
    if not form_data:
        return "Чат не найден", 404

    return render_template("chat.html",
                           form_title=form_data["title"],
                           form_description=form_data["description"],
                           chat_id=chat_id)


@app.route("/api/create_sheet", methods=["POST"])
def api_create_sheet():
    data = request.json
    columns = data.get("columns", [])
    title = data.get("title", "AI Form Responses")
    description = data.get("description", "не указано")
    result = create_user_sheet(columns, title, description)

    # Сохраняем информацию о таблице в сессии пользователя
    if "user_sheets" not in session:
        session["user_sheets"] = []

    session["user_sheets"].append({
        "id": result["id"],
        "url": result["url"],
        "title": result["title"],
        "columns": result["columns"],
        "description": result["description"],
        "chat_id": result["chat_id"]
    })

    session.modified = True

    session["sheet_id"] = result["id"]
    return jsonify(result)


@app.route("/api/chat/<chat_id>/send", methods=["POST"])
def api_chat_send(chat_id):
    """Обработка сообщений в чате с ИИ"""
    if "credentials" not in session:
        return jsonify({"error": "Not authorized"}), 401

    data = request.json
    user_response = data.get("user_response", "")
    previous_question = data.get("previous_question", "")
    current_data = data.get("current_data", {})

    # Получаем описание формы из "БД"
    # table_description = FormDB.get_form_by_chat_id(chat_id)
    table_description = "нет описания"

    if not table_description:
        return jsonify({"error": "Form not found"}), 404

    # Подготавливаем запрос для ИИ
    ai_request = {
        "previous_question": previous_question,
        "user_response": user_response,
        "table_description": table_description,
        "current_data": current_data
    }

    # ai_response = predict(ai_request)
    ai_response = {"question": "вопрос", "data": {"test": "test"}}

    question = ai_response.get("question", "")
    data = ai_response.get("data", "")

    if question == "success":
        # дополняем таблицу
        ...

    return jsonify({"question": question, "data": data})  # во фронтенде проверка на конец диалога


@app.route("/api/update_sheet", methods=["POST"])
def api_update_sheet():
    data = request.json
    spreadsheet_id = session.get("sheet_id")
    if not spreadsheet_id:
        return jsonify({"error": "No active sheet"}), 400
    result = update_user_sheet(spreadsheet_id, data)
    return jsonify(result)


@app.route("/api/list_sheets")
def api_list_sheets():
    # Возвращаем список таблиц пользователя
    return jsonify(session.get("user_sheets", []))


# ======================
# Запуск
# ======================
if __name__ == "__main__":
    app.run(debug=True)
