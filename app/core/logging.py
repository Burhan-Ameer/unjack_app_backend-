import logging

from app.core.config import settings


def setup_logging() -> None:
    """Configure root logger once for consistent app-wide output."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
