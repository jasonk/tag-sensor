import pytest

from tag_sensor.manager import Manager


@pytest.mark.asyncio
async def test_calibration(manager: Manager):
    calibrator = manager.get_calibrator("calibration_camera")
    calibration = await calibrator.calibrate()
    assert calibration


@pytest.mark.asyncio
async def test_calibration_board(manager: Manager):
    calibrator = manager.get_calibrator("calibration_camera")
    calibration = await calibrator.calibrate()
    assert calibration
