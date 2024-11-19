from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Template
import structlog
import yaml

from .camera import CameraConfig, CameraConfigDefaults
from .interfaces import InterfaceConfig
from .marker import MarkerConfig, MarkerConfigDefaults
from .model import Model
from .server.config import MQTTBrokerConfig
from .utils import apply_defaults

logger = structlog.get_logger()


class Config(Model):
    marker_defaults: MarkerConfigDefaults = MarkerConfigDefaults()
    camera_defaults: CameraConfigDefaults = CameraConfigDefaults()

    markers: list[MarkerConfig]
    cameras: list[CameraConfig]

    interfaces: dict[str, InterfaceConfig] = {}
    broker: MQTTBrokerConfig = MQTTBrokerConfig()

    update_interval: float = 60
    camera_data_dir: Path = Path("./camera-data")

    @classmethod
    def load(cls, config_file: Path | str) -> Config:
        file = Path(config_file).resolve()
        tmpl = Template(file.read_text("utf-8"))
        text = tmpl.render(env=os.environ)
        data = yaml.safe_load(text)

        markers = data.pop("markers", [])
        cameras = data.pop("cameras", [])
        data.setdefault("interfaces", {})

        data["markers"] = []
        marker_defaults = data.get("marker_defaults", {}).copy()
        for marker in markers:
            apply_defaults(marker, marker_defaults)
            data["markers"].append(marker)

        data["cameras"] = []
        camera_defaults = data.get("camera_defaults", {}).copy()
        del camera_defaults["interface"]
        for camera in cameras:
            apply_defaults(camera, camera_defaults)
            data["cameras"].append(camera)

        return cls(**data)
