from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property
import json
from pathlib import Path
from time import time
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import BaseClass
from .calibration.calibrator import Calibrator
from .calibration.config import CalibrationConfig
from .calibration.record import CalibrationRecord
from .detection import DetectionData
from .emitter import emit
from .frame import Frame
from .interfaces import Interface, InterfaceConfig
from .marker import Attrs
from .utils import NotFoundError


class HttpOptions(BaseModel):
    url: str | None = None
    url_template: str | None = None
    validate_ssl: bool = True

    model_config = ConfigDict(extra="forbid")


class OverlayOptions(BaseModel):
    marker: bool = True

    # origin: tuple[int, int] = ( 0, 0 )
    color: str = "black"
    outline: str = "white"
    scale: float = 3
    thickness: int = 1
    font: str = "FONT_HERSHEY_SIMPLEX"
    line_spacing: float = 1.5
    line_type: str = "LINE_AA"

    attributes: list[str] = [
        "camera",
        "timestamp",
        "tag_id",
        "edge_length",
        "marker",
        "distance",
        "",
        "message",
    ]

    detection_color: str = "green"
    rejection_color: str = "red"
    mark_rejections: bool = False

    model_config = ConfigDict(extra="forbid")


class CameraConfigDefaults(BaseModel):
    http: HttpOptions | None = None
    overlay: OverlayOptions = OverlayOptions()
    ignore_detections: bool = False

    save_images: bool = False

    calibration: CalibrationConfig = CalibrationConfig()

    data_dir: Path | None = None

    address: str | None = None
    username: str | None = None
    password: str | None = None
    channel: str | int | None = None
    stream: str | None = None
    entity_id: str | None = None

    attributes: Attrs | None = None

    interface: InterfaceConfig | str | None = None
    exclude_from_ui: bool = False


class CameraConfig(CameraConfigDefaults):
    id: str

    connections: list[tuple[str, str]] | None = None


class CameraNotFoundError(NotFoundError):
    def __init__(self, camera_id: str):
        super().__init__(f"Camera not found: {camera_id}")


@dataclass
class Camera(BaseClass):
    config: CameraConfig
    directory: Path
    interface: Interface | None = None

    detection_data: DetectionData | None = None
    message: str | None = None
    calibrator: Calibrator | None = None

    is_available: bool = True

    @property
    def id(self):
        return self.config.id

    @property
    def can_calibrate(self):
        return bool(self.config.calibration)

    @cached_property
    def calibration_file(self) -> Path:
        return self.directory / "calibration.yaml"

    @cached_property
    def calibration(self):
        return CalibrationRecord.load(self.calibration_file)

    @property
    def calibrating(self) -> bool:
        return self.calibrator is not None

    @property
    def original_frame(self) -> Frame | None:
        if self.detection_data is None:
            return None  # pragma: no cover
        return self.detection_data.original_frame

    @property
    def annotated_frame(self) -> Frame | None:
        if self.detection_data is None:
            return None  # pragma: no cover
        return self.detection_data.annotated_frame

    def update_calibration(self, calibration: CalibrationRecord | None):
        if not calibration:
            return None
        self.calibration = calibration
        file = calibration.save(self.calibration_file)
        self.emit("calibration", calibration=calibration, file=file)
        return calibration

    def set_message(self, msg: str | None = None):
        self.message = msg

    def emit(self, event: str, **kwargs):
        emit(f"camera:{event}", camera=self, **kwargs)

    def __str__(self):
        return self.id

    def update(self, data: DetectionData):
        self.detection_data = data

        for detection in data.all_detections:
            self.emit("detection", detection=detection)

        frames: dict[str, Frame] = {
            "original": data.original_frame,
            "annotated": data.annotated_frame,
        }
        for family_data in data.families:
            name = "family:" + family_data.family.group
            frames[name] = family_data.annotated_frame
        self.emit_frames(**frames)

    def emit_frames(self, **frames: Frame):
        now = time()
        for name, frame in frames.items():
            self.emit_frame(name, frame, now)

    def emit_frame(self, name: str, frame: Frame, now: float | None = None):
        if now is None:
            now = time()
        image = frame.to_png()
        self.emit("frame", frame=frame, name=name)
        self.emit("image", image=image, name=name)

        if not self.config.save_images:
            return  # pragma: no cover
        file = self.directory / f"{name}-{now}.png"
        frame.save(file)
        self.emit("image:file", image=image, file=file, name=name)

    @property
    def attributes(self) -> Attrs:
        res: Attrs = {
            "camera_id": self.config.id,
            "calibrating": self.calibrating,
        }
        if images_needed := self.calibrator and self.calibrator.need:
            res.update(
                {
                    "calibrating": bool(images_needed > 0),
                    "images_needed": images_needed,
                }
            )
        if self.config.attributes:
            res.update(self.config.attributes)
        return res

    @property
    def properties(self) -> Attrs:
        res: Attrs = {}
        if data := self.detection_data:
            res.update(data.properties)
        return res

    def configure(self):
        _id = self.config.id

        def make(kind: str, name: str, data: dict[str, Any]):
            topic = f"homeassistant/{kind}/{_id}/{name}/config"
            if self.config.connections:
                data.setdefault("connections", self.config.connections)
            yield (
                topic,
                json.dumps(
                    {
                        "~": self.get_topic(),
                        "unique_id": f"{_id}_{name}",
                        "has_entity_name": True,
                        "state_topic": "~/state",
                        **data,
                    },
                ),
            )

        yield from make(
            "binary_sensor",
            "calibrating",
            {
                "name": "Calibrating",
                "payload_on": "ON",
                "payload_off": "OFF",
                "optimistic": False,
                "entity_category": "config",
                "value_template": "{{ value_json.calibrating }}",
            },
        )
        yield from make(
            "sensor",
            "calibration_images_needed",
            {
                "name": "Calibration Images Needed",
                "entity_category": "diagnostic",
                "step": 1,
                "value_template": "{{ value_json.images_needed }}",
            },
        )

    def get_topic(self, *suffix: str) -> str:
        return "/".join(["tag-sensor", self.config.id, *suffix])

    def publish(self) -> Generator[tuple[str, str], None, None]:
        yield (self.get_topic("state"), json.dumps(self.attributes))
