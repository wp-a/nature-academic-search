"""Stderr-only structured logging that is safe for MCP stdio transports."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for field in ("tool", "query", "sources", "duration_ms", "results_count"):
            value = getattr(record, field, None)
            if value is not None:
                data[field] = value
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("nature-academic-search")
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger
