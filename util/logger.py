import logging
import os
import inspect
from typing import Optional
from datetime import date


class CLogger:
    """
        A robust wrapper around the Python logging module that:
        - Logs to both console and file
        - Automatically tags logs with caller file
        - Supports configurable log levels
    """

    LOG_DIRECTORY = "logs"
    LOG_FILE_NAME = f"application_{str(date.today()).replace('-', '_')}.log"

    def __init__(self, level: Optional[str] = "INFO"):
        # Ensure log directory exists
        os.makedirs(self.LOG_DIRECTORY, exist_ok=True)

        # Determine caller for context-aware logging
        caller_frame = inspect.stack()[1]
        caller_file = os.path.basename(caller_frame.filename)
        self.logger_name = caller_file

        # Create logger instance
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self._get_level(level))

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            self._add_handlers()

    def _get_level(self, level_str: str) -> int:
        return {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }.get(level_str.upper(), logging.INFO)

    def _add_handlers(self):
        log_path = os.path.join(
            self.LOG_DIRECTORY, self.LOG_FILE_NAME)

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
