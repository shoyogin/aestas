"""Single place to configure stdlib logging for the app."""
import logging
import sys

from app.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Attach a stdout handler once; safe to call from several entry points."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
    _CONFIGURED = True
