from __future__ import annotations

from base64 import b64encode
from collections.abc import Generator
from dataclasses import dataclass, field, fields
from functools import cached_property
import json
from typing import Literal

import numpy

from .version import version
from .base import BaseClass
from .detection import Detection
from .emitter import emit
from .family import Family, FamilyGroup
from .frame import Frame
from .model import Model
from .renderer import (
    MarkerPNGConfig,
    MarkerRendererConfig,
    MarkerSTLConfig,
    MarkerSVGConfig,
)
from .utils import NotFoundError

Attr = str | int | float | bool | None
Attrs = dict[str, Attr]


class MarkerConfigDefaults(Model):
    attributes: Attrs = {}

    size: int | None = None
    """
    The size of the marker in millimeters. Used in calculating the
    distance to the marker.
    """

    invert: bool = False
    family: FamilyGroup = "4X4"
    filename: str = "marker-$tag_id"
    label: str | bool = True

    rendering: MarkerRendererConfig | None = None
    stl_rendering: MarkerSTLConfig | None = None
    png_rendering: MarkerPNGConfig | None = None
    svg_rendering: MarkerSVGConfig | None = None

    exclude_from_ui: bool = False
    cameras: list[str] = []

    distance_unit: Literal["mm", "cm", "m", "in", "ft"] = "m"
    distance_decimals: int = 1


class MarkerConfig(MarkerConfigDefaults):
    id: str
    tag_id: int
    name: str | None = None


class MarkerNotFoundError(NotFoundError):
    def __init__(self, marker_id: str | int):
        super().__init__(f"Marker not found: {marker_id}")


@dataclass
class Marker(BaseClass):
    config: MarkerConfig
    detection: Detection | None = None
    detections: list[Detection] | None = None
    original_frame: Frame | None = field(
        init=False,
        repr=False,
        default=None,
    )
    annotated_frame: Frame | None = field(
        init=False,
        repr=False,
        default=None,
    )

    def __str__(self):
        return f"Marker({self.id} - #{self.tag_id})"

    @property
    def kind(self):
        return "marker"

    def update(
        self,
        detections: list[Detection],
        detection: Detection | None,
        original_frame: Frame | None,
        annotated_frame: Frame | None,
    ):
        self.detection = detection
        self.detections = detections
        self.original_frame = original_frame
        self.annotated_frame = annotated_frame
        self.emit("updated")

    @cached_property
    def cameras(self):
        return self.config.cameras

    @cached_property
    def id(self):
        return self.config.id

    def __hash__(self):
        return hash(self.id)

    def emit(self, event: str, **kwargs):
        kwargs["marker"] = self
        emit(f"marker:{event}", **kwargs)

    @property
    def has_detection(self):
        return bool(self.detection)

    @property
    def has_state(self):
        return self.detections is not None

    @property
    def is_on(self):
        if not self.has_state:
            return None
        if self.config.invert:
            return not self.has_detection
        return self.has_detection

    @property
    def attributes(self) -> Attrs:
        res: Attrs = {
            "tag_id": self.config.tag_id,
            "marker_size": self.config.size,
            "inverted": self.config.invert,
            "family": str(self.config.family),
        }
        if self.config.attributes:
            res.update(self.config.attributes)
        if self.detection:
            res.update(self.detection.attributes)
        if self.config.name:
            res["name"] = self.config.name
        if self.config.cameras:
            res["cameras"] = ", ".join(self.config.cameras)
        return res

    @property
    def properties(self) -> Attrs:
        return {
            "has_state": self.has_state,
            "has_detection": self.has_detection,
            "is_on": self.is_on,
        }

    @property
    def distance(self) -> float | None:
        det = self.detection
        if det is None:
            return None
        return det.distance

    @property
    def state(self) -> Literal["ON", "OFF"]:
        return "ON" if self.is_on else "OFF"

    @cached_property
    def family(self):
        return Family(self.config.family)

    @cached_property
    def dictionary(self):
        return self.family.dictionary(self.config.tag_id)

    @cached_property
    def tag_id(self):
        return self.config.tag_id

    @property
    def pose_points(self):
        size = self.config.size
        if not size:
            return None
        return numpy.array(
            [
                [0 - size / 2, 0 + size / 2, 0],
                [0 + size / 2, 0 + size / 2, 0],
                [0 + size / 2, 0 - size / 2, 0],
                [0 - size / 2, 0 - size / 2, 0],
            ],
            dtype=numpy.float32,
        )

    def __rich_repr__(self):
        keys = {f.name for f in fields(self)}
        keys.update(("is_on", "has_state", "has_detection"))
        for key in keys:
            yield key, getattr(self, key, None), None

    def get_b64_png(self):
        detection = self.detection
        if detection is None:
            return None
        frame = detection.annotated_frame
        if frame is None:
            return None  # pragma: no cover

        image = frame.to_image("png")
        return b64encode(image).decode()

    def get_homeassistant_device_config(self):
        name = self.config.name
        _id = self.config.id
        tag_id = self.config.tag_id
        common = {
            "~": self.get_topic(),
            "json_attributes_topic": "~/attributes",
            "has_entity_name": True,
            "state_topic": "~/state",
            "availability": [
                {
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "topic": "tag-sensor/availability",
                },
                #               {
                #                   "payload_available": "online",
                #                   "payload_not_available": "offline",
                #                   "topic": "~/availability",
                #               },
            ],
            "availability_mode": "all",
        }
        return {
            "device": {
                "name": name,
                "manufacturer": "Tag Sensor",
                "model": "Tag Sensor Marker",
                "identifiers": [_id, f"aruco:{tag_id}"],
                "sw_version": version,
            },
            "origin": {
                "name": "Tag Sensor",
                "sw_version": version,
                "support_url": "https://github.com/jasonk/tag-sensor",
            },
            # 'configuration_url': self.configuration_url,
            "components": {
                f"{_id}_image": {
                    "platform": "image",
                    "name": "Image",
                    "image_topic": "~/image",
                    "object_id": f"{_id}_image",
                    "image_encoding": "b64",
                    "content_type": "image/png",
                    "icon": "mdi:tag",
                    "unique_id": f"{_id}_image",
                    **common,
                },
                f"{_id}_active": {
                    "platform": "binary_sensor",
                    "name": None,
                    "object_id": f"{_id}_active",
                    "icon": "mdi:tag",
                    "unique_id": f"{_id}_binary_sensor",
                    "payload_off": "OFF",
                    "payload_on": "ON",
                    "value_template": "{{ value_json.state }}",
                    **common,
                },
                f"{_id}_distance": {
                    "platform": "sensor",
                    "object_id": f"{_id}_distance",
                    "device_class": "distance",
                    "icon": "mdi:tag",
                    "name": "Distance",
                    "unique_id": f"{_id}_sensor",
                    "suggested_display_precision": 0,
                    "native_unit_of_measurement": "m",
                    "value_template": "{{ value_json.distance }}",
                    **common,
                },
            },
        }

    def configure(self):
        topic = f"homeassistant/device/{self.config.id}/config"
        yield topic, json.dumps(self.get_homeassistant_device_config())

    def get_topic(self, *suffix: str) -> str:
        return "/".join(["tag-sensor", self.config.id, *suffix])

    def publish(self) -> Generator[tuple[str, str], None, None]:
        # yield self.get_topic("availability"), "online"

        attributes = json.dumps(self.attributes)
        yield self.get_topic("attributes"), attributes

        state = json.dumps({"state": self.state, "distance": self.distance})
        yield self.get_topic("state"), state

        image = self.get_b64_png()
        if image:
            yield self.get_topic("image"), image
