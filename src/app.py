from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import requests

app = Flask(__name__)
app.template_folder = "frontend/templates"

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
    return {"id": spreadsheet_id, "url": url, "title": title, "columns": columns, "description": description}


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
        "description": result["description"]
    })

    # Важно: сохраняем изменения в сессии
    session.modified = True

    session["sheet_id"] = result["id"]
    return jsonify(result)


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
