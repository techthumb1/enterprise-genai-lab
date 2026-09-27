from __future__ import annotations

import logging
import sys

import logfire

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure standard logging and Logfire observability."""

    log_level = logging.getLevelNamesMapping()[settings.log_level]

    logfire.configure(
        service_name="enterprise-genai-lab",
        environment=settings.environment,
        send_to_logfire=False,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )

    logfire_handler = logfire.LogfireLoggingHandler()
    logfire_handler.setLevel(log_level)

    logging.basicConfig(
        level=log_level,
        handlers=[
            console_handler,
            logfire_handler,
        ],
        force=True,
    )