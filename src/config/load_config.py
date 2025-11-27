from dotenv import load_dotenv
from pydantic import ValidationError

import os
import logging

from .config_models import ConfigModel


def load_config() -> ConfigModel:
    load_dotenv() 

    config_data: dict = {
        "PostgreSQL": {
            "host": os.getenv("POSTGRES_HOST"),
            "port": os.getenv("POSTGRES_PORT"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "db": os.getenv("POSTGRES_DB"),
        },
        "DeepSeek": {
            "apikey": os.getenv("DEEPSEEK_APIKEY"),
            "baseurl": os.getenv("DEEPSEEK_BASEURL"),
            "model_type": os.getenv("DEEPSEEK_MODELTYPE"),
        },
        "FlaskServer": {
            "host": os.getenv("SERVER_HOST", "localhost"),
            "port": int(os.getenv("SERVER_PORT", 8080)),
        },
        "GoogleAPIs": {
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_url": os.getenv("REDIRECT_URI"),
        },
        "Logger":
        {
            "logger_mode": os.getenv("LOGGER_MODE", "DEBUG"),
            "logger_file": os.getenv("LOGGER_FILE", "CONSOLE")

        }
    }
    
    # Валидация конфигов
    try:
        config_model = ConfigModel(**config_data)
        return config_model  # отвалидирован
    
    except ValidationError as e:
        error_lines = [
            f" - {'.'.join(map(str, err['loc']))}: {err['msg']}"
            for err in e.errors()
        ]
        full_message = "Ошибка валидации:\n" + "\n".join(error_lines)
        logging.critical(full_message)
        
        exit(-1)
