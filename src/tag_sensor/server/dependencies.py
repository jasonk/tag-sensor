from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
import structlog

from tag_sensor.camera import Camera as CameraType
from tag_sensor.manager import Manager as ManagerType
from tag_sensor.marker import Marker as MarkerType

from .mqtt import MQTTHelper

logger = structlog.get_logger()


def _get_manager(request: Request):
    return request.state.manager


def _get_mqtt(request: Request):
    return request.state.mqtt


def _get_camera(manager: Manager, camera_id: str):
    camera = manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if camera.config.exclude_from_ui:
        return None
    return camera


def _get_marker(manager: Manager, marker_id: str):
    marker = manager.get_marker(marker_id)
    if not marker or marker.config.exclude_from_ui:
        raise HTTPException(status_code=404, detail="Marker not found")
    return marker


def _get_cameras(manager: Manager):
    return [
        camera
        for camera in manager.cameras
        if camera.config.exclude_from_ui is False
    ]


def _get_markers(manager: Manager):
    return [
        marker
        for marker in manager.markers
        if marker.config.exclude_from_ui is False
    ]


def app_context(request: Request) -> dict[str, Any]:
    manager = _get_manager(request)
    return {
        "manager": manager,
        "markers": _get_markers(manager),
        "cameras": _get_cameras(manager),
    }


Camera = Annotated[CameraType, Depends(_get_camera)]
Cameras = Annotated[list[CameraType], Depends(_get_cameras)]
MQTT = Annotated[MQTTHelper, Depends(_get_mqtt)]
Manager = Annotated[ManagerType, Depends(_get_manager)]
Marker = Annotated[MarkerType, Depends(_get_marker)]
Markers = Annotated[list[MarkerType], Depends(_get_markers)]
