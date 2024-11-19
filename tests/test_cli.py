import os

from pathlib import Path
from typer.testing import CliRunner

from tag_sensor.__main__ import app

from .utils import lines
from .conftest import CONFIG

runner = CliRunner()

os.environ["CAMERA_USERNAME"] = "test-camera-user"


def run(*args: str, config: Path = CONFIG):
    return runner.invoke(app, [f"--config={config}", *args])


def test_app():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "[OPTIONS] COMMAND [ARGS]" in result.stdout

    result = run()
    assert result.exit_code == 2
    assert "Missing command" in result.stdout


def test_config():
    result = run("config")
    assert result.exit_code == 0
    assert "broker=MQTTBrokerConfig" in result.stdout


def test_cameras():
    result = run("cameras")
    assert result.exit_code == 0
    assert lines(result.stdout) == lines("""
        bins_camera
        calibration_camera
        driveway_camera
        fake_camera
        garage_camera
        mystery_camera
        test_camera
    """)


def test_camera():
    result = run("camera", "bins_camera")
    assert result.exit_code == 0
    assert "bins_camera" in result.stdout


def test_markers():
    result = run("markers")
    assert result.exit_code == 0
    assert lines(result.stdout) == lines("""
        21 recycling_bin_parked
        22 trash_bin_parked
        23 compost_bin_parked
        30 garage_door_open
        40 test_tag
        70 van_in_garage
        71 car_in_garage
    """)


def test_marker():
    res1 = run("marker", "21")
    assert res1.exit_code == 0
    res2 = run("marker", "recycling_bin_parked")
    assert res2.exit_code == 0
    # assert "name='Recycling Bin Parked'" in res1.stdout
    # assert "name='Recycling Bin Parked'" in res2.stdout
    assert "Recycling Bin Parked" in res1.stdout
    assert "Recycling Bin Parked" in res2.stdout
    assert res1.stdout == res2.stdout


def test_show_markers():
    res1 = run("show-markers", "21")
    assert res1.exit_code == 0
    assert lines(res1.stdout) == lines("""
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓░░▓░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
        21 : Recycling Bin Parked
    """)

    res2 = run("show-markers", "recycling_bin_parked")
    assert res2.exit_code == 0
    assert lines(res2.stdout) == lines("""
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓░░▓░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
        21 : Recycling Bin Parked
    """)

    res3 = run("show-markers", "21-22,30,333")
    assert res3.exit_code == 0
    assert lines(res3.stdout) == lines("""
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓░░▓░░░▓
        ▓░▓▓░▓░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
        21 : Recycling Bin Parked
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░░░▓▓░▓
        ▓░░░▓▓░▓
        ▓░▓░▓▓░▓
        ▓░▓░▓░░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
        22 : Trash Bin Parked
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░░░▓░░▓
        ▓░░░▓░░▓
        ▓░▓░░░░▓
        ▓░▓░▓░░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
        30 : Garage Door is Open
        ▓▓▓▓▓▓▓▓
        ▓░░░░░░▓
        ▓░░░▓▓░▓
        ▓░▓░░░░▓
        ▓░▓░▓░░▓
        ▓░▓▓▓░░▓
        ▓░░░░░░▓
        ▓▓▓▓▓▓▓▓
           333
    """)

    res4 = run("show-markers", "50", "--family=10X10")
    assert res4.exit_code == 1

    res5 = run("show-markers")
    assert res5.exit_code == 0


def test_detections():
    result = run("detections")
    assert result.exit_code == 0
    assert lines(result.stdout) == lines("""
        trash_bin_parked - bins_camera
        recycling_bin_parked - bins_camera
        van_in_garage - garage_camera
        garage_door_open - garage_camera
        test_tag - test_camera
    """)


def test_update_once():
    res1 = run(
        "update-once",
        "--no-images",
        "--no-attrs",
        "--updates",
    )
    assert res1.exit_code == 0
    assert lines(res1.stdout) == lines("""
        Updating marker: recycling_bin_parked True
        Updating marker: trash_bin_parked True
        Updating marker: compost_bin_parked False
        Updating marker: garage_door_open False
        Updating marker: van_in_garage False
        Updating marker: car_in_garage True
        Updating marker: test_tag True
    """)

    res2 = run("update-once", "--images", "--attrs")
    assert res2.exit_code == 0


def test_make_stl_markers(tmp_path: Path):
    stls = (
        tmp_path / "marker-22.stl",
        tmp_path / "marker-22.white.stl",
        tmp_path / "marker-22.black.stl",
        tmp_path / "marker-22.guide.stl",
    )
    scad = tmp_path / "marker-22.scad"

    for file in (*stls, scad):
        assert not file.exists()
    result = run("make-stl-markers", "22", f"--directory={tmp_path}")
    assert result.exit_code == 0
    for file in stls:
        assert file.exists()
    assert not scad.exists()


def test_make_png_markers(tmp_path: Path):
    file = tmp_path / "marker-21.png"
    assert not file.exists()
    result = run("make-png-markers", "21", f"--directory={tmp_path}")
    assert result.exit_code == 0
    assert file.exists()


def test_make_svg_markers(tmp_path: Path):
    file = tmp_path / "marker-23.svg"
    assert not file.exists()
    result = run(
        "make-svg-markers",
        "compost_bin_parked",
        f"--directory={tmp_path}",
    )
    assert result.exit_code == 0
    assert file.exists()


def test_make_invalid_marker():
    res1 = run("make-svg-markers", "does_not_exist")
    assert res1.exit_code == 1

    res2 = run("make-svg-markers", "666", "--family=1X1")
    assert res2.exit_code == 1


def test_parse_ids():
    from tag_sensor.__main__ import parse_ids

    assert list(parse_ids(["1", "3-5", "foo"])) == [1, 3, 4, 5, "foo"]


def test_make_calibration_board(tmp_path: Path):
    board = tmp_path / "calibration_camera-calibration-board.png"

    assert not board.exists()
    result = run(
        "make-calibration-board", "calibration_camera", f"--output={board}",
    )
    assert result.exit_code == 0
    assert board.exists()
