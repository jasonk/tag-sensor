import pytest

from tag_sensor.manager import Manager
from tag_sensor.marker import MarkerNotFoundError, Marker, MarkerConfig


@pytest.mark.asyncio
async def test_regular_marker(manager: Manager):
    marker = manager.marker("recycling_bin_parked")
    assert marker.attributes == {
        "tag_id": 21,
        "marker_size": 150,
        "inverted": False,
        "family": "4X4",
        "name": "Recycling Bin Parked",
    }
    assert marker.is_on is None
    await manager.update_detections()
    assert marker.is_on is True
    assert str(marker) == "Marker(recycling_bin_parked - #21)"


@pytest.mark.asyncio
async def test_invalid_markers(manager: Manager):
    with pytest.raises(MarkerNotFoundError):
        manager.marker("invalid_marker")


@pytest.mark.asyncio
async def test_inverted_marker(manager: Manager):
    marker = manager.marker("garage_door_open")
    assert marker.attributes == {
        "tag_id": 30,
        "marker_size": 186,
        "inverted": True,
        "family": "4X4",
        "name": "Garage Door is Open",
        "cameras": "garage_camera",
    }
    assert marker.properties == {
        "has_detection": False,
        "has_state": False,
        "is_on": None,
    }
    await manager.update_detections()
    assert marker.properties == {
        "has_detection": True,
        "has_state": True,
        "is_on": False,
    }


@pytest.mark.asyncio
async def test_camera_specific_marker(manager: Manager):
    marker = manager.marker(40)
    assert marker.attributes == {
        "tag_id": 40,
        "marker_size": 100,
        "inverted": False,
        "family": "4X4",
        "name": "Test Tag",
        "cameras": "test_camera",
    }
    assert marker.properties == {
        "has_detection": False,
        "has_state": False,
        "is_on": None,
    }
    await manager.update_detections()
    assert marker.properties == {
        "has_detection": True,
        "has_state": True,
        "is_on": True,
    }


def test_fake_marker():
    marker = Marker(
        MarkerConfig(
            id="fake_marker",
            tag_id=999,
        ),
    )
    assert marker.pose_points is None
