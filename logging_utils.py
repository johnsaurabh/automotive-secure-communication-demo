from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
            "event": getattr(record, "event", "application_event"),
            "message": record.getMessage(),
        }
        details = getattr(record, "details", None)
        if details:
            payload["details"] = details
        return json.dumps(payload, separators=(",", ":"))


def build_logger(name: str, log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger


def redact_message(message: str) -> str:
    if len(message) <= 10:
        return "<redacted>"
    return f"{message[:4]}...{message[-4:]}"
