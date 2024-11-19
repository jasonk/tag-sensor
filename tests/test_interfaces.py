import pytest
from pathlib import Path

from tag_sensor.manager import Manager
from tag_sensor.interfaces import (
    make_interface,
    DummyInterfaceConfig,
    DummyInterface,
    HttpInterfaceConfig,
    HttpInterface,
    HomeAssistantInterfaceConfig,
    HomeAssistantInterface,
    ScriptInterfaceConfig,
    ScriptInterface,
    ReolinkCameraInterfaceConfig,
    ReolinkCameraInterface,
    ReolinkNvrInterfaceConfig,
    ReolinkNvrInterface,
    HttpInterfaceTemplateConfig,
)


@pytest.mark.asyncio
async def test_dummy_interface():
    config = DummyInterfaceConfig(
        directory=str(Path(__file__).parent / "images"),
    )
    iface = make_interface(config)
    assert isinstance(iface, DummyInterface)

    assert callable(iface.get_frame)


@pytest.mark.asyncio
async def test_http_interface():
    config = HttpInterfaceConfig(
        template=HttpInterfaceTemplateConfig(
            url="https://example.com/",
        ),
    )
    iface = make_interface(config)
    assert isinstance(iface, HttpInterface)

    assert callable(iface.get_frame)


def test_homeassistant_interface():
    config = HomeAssistantInterfaceConfig()
    iface = make_interface(config)
    assert isinstance(iface, HomeAssistantInterface)

    assert callable(iface.get_frame)


async def test_script_interface_shell(manager: Manager):
    config = ScriptInterfaceConfig(command='echo "/dev/null"')
    iface = make_interface(config)
    assert isinstance(iface, ScriptInterface)

    camera = manager.camera("calibration_camera")

    assert callable(iface.get_frame)
    file = await iface.run_command(camera)
    assert file == "/dev/null"


async def test_script_interface_exec(manager: Manager):
    config = ScriptInterfaceConfig(command=["echo", "/dev/null"])
    iface = make_interface(config)
    assert isinstance(iface, ScriptInterface)

    camera = manager.camera("calibration_camera")

    assert callable(iface.get_frame)
    file = await iface.run_command(camera)
    assert file == "/dev/null"


def test_reolink_camera_interface():
    config = ReolinkCameraInterfaceConfig()
    iface = make_interface(config)
    assert isinstance(iface, ReolinkCameraInterface)

    assert callable(iface.get_frame)


def test_reolink_nvr_interface():
    config = ReolinkNvrInterfaceConfig(
        address="127.0.0.1",
    )
    iface = make_interface(config)
    assert isinstance(iface, ReolinkNvrInterface)

    assert callable(iface.get_frame)
