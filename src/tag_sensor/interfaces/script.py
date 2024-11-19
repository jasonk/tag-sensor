from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import structlog

from tag_sensor.frame import Frame
from tag_sensor.utils import fill_template

from .base import BaseInterface, BaseInterfaceConfig

if TYPE_CHECKING:
    from tag_sensor.camera import Camera

logger = structlog.get_logger()


class ScriptInterfaceConfig(BaseInterfaceConfig):
    provider: Literal["script"] = "script"

    command: str | list[str]


@dataclass
class ScriptInterface(BaseInterface[ScriptInterfaceConfig]):
    async def run_command(self, camera: Camera):
        conf = camera.config.model_dump()
        if isinstance(self.config.command, list):
            proc = await asyncio.create_subprocess_exec(
                *(fill_template(c, conf) for c in self.config.command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_shell(
                fill_template(self.config.command, conf),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        stdout, stderr = await proc.communicate()
        if stderr:  # pragma: no cover
            logger.error("Error running script", stderr=stderr.decode())
        return stdout.decode().strip()

    async def get_frame(self, camera: Camera):  # pragma: no cover
        file = await self.run_command(camera)
        return Frame.from_file(file)
