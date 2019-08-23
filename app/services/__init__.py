from .logging import logging
from .devrant import DevRantService
from .router_service import RouterService

dev_rant_service = DevRantService()
router_service = RouterService()

__all__ = (
    'logging',
    'dev_rant_service',
    'router_service',
)
