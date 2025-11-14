import atexit

from .connect_db import connect_db, disconnect_db

atexit.register(disconnect_db)  # disconnect_db will be triggered when script crashes


__all__ = [
    "connect_db",
    "disconnect_db"
]
