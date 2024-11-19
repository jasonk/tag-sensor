import pytest
from typing import Protocol
from pathlib import Path
import os

from tag_sensor.manager import Manager
from tag_sensor.camera import Camera, CameraConfig

REPO_DIR = Path(__file__).parent.parent
CONFIG = REPO_DIR / "test-config.yaml"
os.environ["TAG_SENSOR_CONFIG"] = str(CONFIG)


@pytest.fixture
async def manager() -> Manager:
    mgr = Manager()
    mgr.load_config("./test-config.yaml")
    await mgr.prepare()
    return mgr


@pytest.fixture
def config(manager: Manager):
    return manager.config


@pytest.fixture
def images():
    return Path(__file__).parent / "images"


class MakeCamera(Protocol):
    def __call__(
        self,
        camera_id: str | None = None,
        **kwargs,
    ) -> Camera: ...


@pytest.fixture
def make_camera(tmp_path: Path):
    def _make_camera(camera_id: str = "test_camera", **kwargs):
        return Camera(
            CameraConfig(
                id=camera_id,
                **kwargs,
            ),
            directory=tmp_path,
        )

    return _make_camera
