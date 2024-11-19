
from tag_sensor.config import Config


def test_config():
    config = Config.load("test-config.yaml")

    assert config is not None
    assert len(config.cameras) == 7
    assert len(config.markers) == 7

    rendering = config.markers[0].rendering
    assert rendering is not None
    assert rendering.size == 25
    assert rendering.label == "$tag_id - $name"
