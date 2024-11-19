import pytest

from tag_sensor.manager import Manager


@pytest.mark.asyncio
async def test_misc_detection(manager: Manager):
    camera = manager.camera("bins_camera")

    data = await manager.get_detection_data_for_camera(camera)
    assert data is not None

    family1 = data.family("4X4")
    assert family1 is not None
    assert family1.group == "4X4"

    family2 = data.family("5X5")
    assert family2 is None

    detection = family1.detections[0]
    assert detection is not None
    assert detection.marker is not None
    assert detection.marker.id == "trash_bin_parked"

    detection.raw_distance = 1000
    assert detection.sort_distance == 1000

    detection.raw_distance = None
    del detection.sort_distance
    assert detection.sort_distance > 100000

    detection.pose = None
    del detection.rvec
    del detection.tvec
    del detection.raw_distance
    assert detection.rvec is None
    assert detection.tvec is None
    assert detection.raw_distance is None

    assert list(detection.warnings()) == []

    detection.marker.config.size = 0
    assert list(detection.warnings()) == [
        "Marker size not defined, cannot compute distance",
    ]

    detection.marker = None
    detection.camera.calibration = None

    assert list(detection.warnings()) == [
        "No marker associated, cannot compute distance",
        "No camera calibration, cannot compute distance",
    ]
