from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from tag_sensor.model import Model

if TYPE_CHECKING:
    from tag_sensor.camera import Camera
    from tag_sensor.frame import Frame


class BaseInterfaceConfig(Model):
    pass


ConfigT = TypeVar("ConfigT", bound=BaseInterfaceConfig)


@dataclass
class BaseInterface(ABC, Generic[ConfigT]):
    config: ConfigT

    @abstractmethod
    async def get_frame(self, camera: Camera) -> Frame | None: ...

    async def start(self):
        pass

    async def stop(self):
        pass
