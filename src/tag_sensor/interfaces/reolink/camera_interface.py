from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import structlog

from .base import ReolinkBaseInterface, ReolinkBaseInterfaceConfig

logger = structlog.get_logger()


class ReolinkCameraInterfaceConfig(ReolinkBaseInterfaceConfig):
    provider: Literal["reolink"] = "reolink"


@dataclass
class ReolinkCameraInterface(
    ReolinkBaseInterface[ReolinkCameraInterfaceConfig],
):
    pass
