from typing import Optional

from sqlalchemy import Connection

from .db import engine
from .entity.base_entity import Base

conn: Optional[Connection] = None


def connect_db():
    print("Connect to database")
    engine.connect()

    Base.metadata.create_all(engine)


def disconnect_db():
    print("Disconnect from database")
    if conn is not None:
        conn.close()
