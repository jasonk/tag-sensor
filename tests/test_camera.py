import pytest

from tag_sensor.manager import Manager
from tag_sensor.camera import CameraNotFoundError


@pytest.mark.asyncio
async def test_invalid_cameras(manager: Manager):
    with pytest.raises(CameraNotFoundError):
        manager.camera("invalid_camera")


@pytest.mark.asyncio
async def test_regular_camera(manager: Manager):
    camera = manager.camera("bins_camera")
    assert camera.attributes == {
        "camera_id": "bins_camera",
        "calibrating": False,
    }
    assert camera.properties == {}
    await manager.update_detections()
    assert camera.properties == {
        "detections": 2,
        "markers": "trash_bin_parked recycling_bin_parked",
    }

    assert str(camera) == "bins_camera"
    assert camera.update_calibration(None) is None
