from pathlib import Path

from tag_sensor.frame import Frame


def test_frame(tmp_path: Path, images: Path):
    frame = Frame.from_file(str(images / "test_camera.png"))
    assert frame

    frame.save(tmp_path / "test_frame.png")
