"""Privacy-conscious logging for AI benchmark runs.

Only metadata is logged: test/case/run identifiers, provider, model,
latency and error status. Prompts, CVs, model outputs and secrets are excluded.
"""

import logging
import sys

LOGGER_NAME = "academic_platform.ai_benchmark"


def configure_benchmark_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure console logging once without duplicating handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if not any(getattr(handler, "_benchmark_handler", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        handler._benchmark_handler = True
        logger.addHandler(handler)

    return logger


logger = configure_benchmark_logging()