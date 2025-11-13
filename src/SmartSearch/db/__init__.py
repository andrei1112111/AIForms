from config import config
from .database import DataBase

database = DataBase(config.PostgreSQL) 

__all__ = [
    "database"
]
