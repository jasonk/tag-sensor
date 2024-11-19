from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tag_sensor.camera import Camera


@dataclass
class ReolinkNvrStream:
    name: str
    height: int
    width: int


@dataclass
class ReolinkNvrChannel:
    channel: int
    name: str
    online: bool
    sleep: bool
    uid: str
    streams: list[ReolinkNvrStream]

    def matches(self, camera: Camera):
        return camera.config.channel in (self.channel, self.name)

    def stream(self, name: str):
        for stream in self.streams:
            if stream.name == name:
                return stream
        return None
