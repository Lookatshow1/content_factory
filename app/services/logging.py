import json
import logging
from typing import Any


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","time":"%(asctime)s","message":%(message)s}',
    )


def log_event(logger: logging.Logger, event: str, **fields: Any):
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))
