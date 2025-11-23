from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from config import config


sqllogger = logging.getLogger("sqlalchemy.engine.Engine.engine")
sqllogger.setLevel(logging.WARNING)



engine = create_engine(
    "postgresql+psycopg2://postgres:43720@localhost:5432/aiforms",
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
    print(f"Success.")
except SQLAlchemyError as e:
    print(f"Failed : {e}")
    raise RuntimeError("Failed connection to db")
