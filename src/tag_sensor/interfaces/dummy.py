from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from tag_sensor.frame import Frame

from .base import BaseInterface, BaseInterfaceConfig

if TYPE_CHECKING:
    from tag_sensor.camera import Camera


class DummyInterfaceConfig(BaseInterfaceConfig):
    provider: Literal["dummy"] = "dummy"
    directory: str


@dataclass
class DummyInterface(BaseInterface[DummyInterfaceConfig]):
    names: dict[str, list[Path]] = field(default_factory=dict)

    async def get_frame(self, camera: Camera):
        camera_id = camera.config.id
        subdir = Path(self.config.directory) / camera_id
        if subdir.is_dir():
            if camera_id not in self.names:
                self.names[camera_id] = list(subdir.glob("*.png"))
            names = self.names.get(camera_id)
            if names:
                return Frame.from_file(str(names.pop(0)))
        file = subdir.with_suffix(".png")
        if file.is_file():
            return Frame.from_file(str(file))
        return None
