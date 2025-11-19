from __future__ import annotations

import logging
import os
from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    os.makedirs("logs", exist_ok=True)
    json_logging = os.getenv("LOG_JSON", "false").lower() == "true"
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "asctime: %(asctime)s level: %(levelname)s name: %(name)s message: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if json_logging else "default",
                    "level": level,
                },
                "app_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "json" if json_logging else "default",
                    "filename": "logs/app.log",
                    "maxBytes": 1048576,
                    "backupCount": 3,
                    "level": level,
                    "encoding": "utf-8",
                },
                "legacy_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "json" if json_logging else "default",
                    "filename": "logs/legacy_import.log",
                    "maxBytes": 1048576,
                    "backupCount": 3,
                    "level": level,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "app_file"],
                "level": level,
            },
            "loggers": {
                "legacy.import": {
                    "handlers": ["console", "legacy_file"],
                    "level": level,
                    "propagate": False,
                }
            },
        }
    )
