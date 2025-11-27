from pydantic import BaseModel


class DeepSeekConfigModel(BaseModel):
    """моделька под подключение к api DeepSeek'а"""
    apikey: str
    baseurl: str
    model_type: str

class GoogleAPIs(BaseModel):
    """моделька под подключение к api google'а"""
    google_client_id: str
    google_client_secret: str
    redirect_url: str

class FlaskServer(BaseModel):
    """моделька под настройки фласка"""
    host: str
    port: int

class PostgresConfigModel(BaseModel):
    """моделька под подключение к бд через psycpg"""
    host: str
    port: int
    user: str
    password: str
    db: str

class LoggingConfigModel(BaseModel):
    logger_mode: str
    logger_file: str

class ConfigModel(BaseModel):
    PostgreSQL: PostgresConfigModel
    DeepSeek: DeepSeekConfigModel
    Logger: LoggingConfigModel
    FlaskServer: FlaskServer
    GoogleAPIs: GoogleAPIs
 
    model_config = { # pydantic v2
        "arbitrary_types_allowed": True
    }
