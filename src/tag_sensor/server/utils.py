from __future__ import annotations

from asyncio import Event

import structlog

logger = structlog.get_logger()

shutting_down = Event()
