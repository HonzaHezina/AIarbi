import logging
import os
import sys
from typing import Optional

"""
Centralized logging configuration for the project.

Usage:
    from utils.logging_config import setup_logging, get_logger
    setup_logging()  # optional: setup_logging(level=logging.DEBUG)
    logger = get_logger(__name__)
"""

def setup_logging(level: Optional[int] = None):
    """Configure root logging for the application.

    This sets an explicit StreamHandler to stdout so logs appear correctly
    in Hugging Face Spaces and other hosted environments. It respects the
    LOG_LEVEL environment variable (e.g. LOG_LEVEL=DEBUG).
    """
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)

    # Configure root logger and explicit stdout StreamHandler for HF Spaces
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicate logs when re-initializing
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    
    def _sanitize(s: str) -> str:
        """Remove non-ASCII characters (emojis, fancy symbols) to avoid console encoding errors."""
        try:
            return ''.join(ch for ch in s if ord(ch) < 128)
        except Exception:
            return s
    
    class SanitizingFormatter(logging.Formatter):
        """Formatter that sanitizes the final message to remove characters unsupported by some consoles."""
        def format(self, record):
            try:
                # Produce the message, then sanitize it.
                message = record.getMessage()
                safe = _sanitize(str(message))
                # Temporarily set record.message so formatting uses sanitized text
                record.msg = safe
                record.args = ()
            except Exception:
                pass
            return super().format(record)
    
    formatter = SanitizingFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Reduce verbosity of very noisy third-party libraries
    for noisy in ["ccxt", "web3", "urllib3", "asyncio"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Example: set gradio and plotly to INFO to avoid DEBUG spam
    logging.getLogger("gradio").setLevel(logging.INFO)
    logging.getLogger("plotly").setLevel(logging.INFO)


def get_logger(name: str):
    """Helper to get a module logger."""
    return logging.getLogger(name)