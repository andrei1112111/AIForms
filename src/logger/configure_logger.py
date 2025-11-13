from logging import INFO, DEBUG, StreamHandler, FileHandler,  Formatter, getLogger
from sys import stdout
import os
import pytz
from datetime import datetime

class TZFormatter(Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        """Custom log formatter that supports timezone-aware timestamps"""
        super().__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):
        """Overrides default time formatting to use the configured timezone"""
        dt = datetime.fromtimestamp(record.created, self.tz)

        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()
    

from logging import INFO, DEBUG, StreamHandler, FileHandler,  Formatter, getLogger
from sys import stdout

import pytz
from datetime import datetime


class TZFormatter(Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        """Custom log formatter that supports timezone-aware timestamps"""
        super().__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):
        """Overrides default time formatting to use the configured timezone"""
        dt = datetime.fromtimestamp(record.created, self.tz)

        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()
    

def configure_logger(tz_name: str = "UTC", logger_mode: str = "DEBUG", file_name: str = None):

    logger = getLogger()
    logger.handlers.clear()

    if logger_mode == "DEBUG":
        logger.setLevel(DEBUG)
    else:
        logger.setLevel(INFO)

    formatter = TZFormatter(
        fmt="%(asctime)s %(levelname)s [%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        tz=pytz.timezone(tz_name)
    )

    if file_name == "CONSOLE":
        console_handler = StreamHandler(stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        if not os.path.exists("src/logger/logs"):
            os.makedirs("src/logger/logs", exist_ok=True)
        path_to_file = os.path.join("src/logger/logs", file_name)
        file_handler = FileHandler("src/logger/logs/app.log",encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)  
  
    return logger