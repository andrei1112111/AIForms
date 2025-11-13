"""
Валидация конфигов на Pydantic V2

Содержит:
    DeepSeekModel
    PostgreSQLModel

Использование:
    config.DeepSeek.apikey
    ...
"""
from .config_models import ConfigModel
from .load_config import load_config


config: ConfigModel = load_config()

__all__ = [
    "config"
]
