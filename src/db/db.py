from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging


sqllogger = logging.getLogger("sqlalchemy.engine.Engine.engine")
sqllogger.setLevel(logging.WARNING)


engine = create_engine(
    "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
        "forms_user",
        "forms_pass",
        "127.0.0.1",
        5433,
        "metrics_db",
    ),
    pool_size=5,
    max_overflow=10,
    echo=False,
    pool_logging_name="engine",
    logging_name="engine",
)

# check db connection
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"Успешное подключение к базе тикетов .")
except SQLAlchemyError as e:
    print(f"Ошибка подключения к базе : {e}")
    raise RuntimeError("Failed connection to db")
