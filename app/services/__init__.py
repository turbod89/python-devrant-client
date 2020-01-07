from .logging import logging
from .devrant import DevRantService

dev_rant_service = DevRantService()

__all__ = (
    'logging',
    'dev_rant_service',
)
