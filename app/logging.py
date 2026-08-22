import json
import logging
from datetime import UTC, datetime
from math import isfinite
from typing import TypeGuard

JsonPrimitive = str | int | float | bool


class JsonFormatter(logging.Formatter):
    """Renderiza eventos de error de SensorHub como una sola línea JSON."""

    _event_fields = (
        "event",
        "status_code",
        "path",
        "method",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, JsonPrimitive] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }
        for field in self._event_fields:
            value = getattr(record, field, None)
            if is_safe_log_value(value):
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def is_safe_log_value(value: object) -> TypeGuard[JsonPrimitive]:
    if isinstance(value, (str, int, bool)):
        return True
    return isinstance(value, float) and isfinite(value)


def configure_app_logging() -> None:
    """Configura una única salida JSON para el logger propio de la aplicación."""

    logger = logging.getLogger("app")
    logger.propagate = False
    if any(
        getattr(handler, "_sensorhub_json_handler", False)
        for handler in logger.handlers
    ):
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler._sensorhub_json_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
