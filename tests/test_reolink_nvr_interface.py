import pytest
from pydantic import SecretStr
from typing import Any, Protocol
from pytest_httpx import HTTPXMock

from tag_sensor.interfaces import ReolinkNvrInterface, ReolinkNvrInterfaceConfig


class MockCmd(Protocol):
    def __call__(
        self,
        cmd: str,
        param: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        token: str | None = None,
        method: str | None = None,
    ) -> None: ...


class MockCmds(Protocol):
    def __call__(
        self,
        cmd: str,
        params: list[dict[str, Any]],
        results: list[dict[str, Any]],
        token: str | None = None,
        method: str | None = None,
    ) -> None: ...


@pytest.fixture
def mock_cmd(httpx_mock: HTTPXMock):
    def _mock_cmd(
        cmd: str,
        result: dict[str, Any],
        param: dict[str, Any] | None = None,
        token: str = "fake-token",  # noqa: S107
        method: str = "POST",
    ):
        if param is None:
            param = {}
        httpx_mock.add_response(
            url=f"https://example.com/cgi-bin/api.cgi?cmd={cmd}&token={token}",
            method=method,
            match_json=[{"cmd": cmd, "action": 0, "param": param}],
            json=[
                {
                    "cmd": cmd,
                    "code": 0,
                    "value": result,
                },
            ],
        )

    return _mock_cmd


@pytest.fixture
def mock_cmds(httpx_mock: HTTPXMock):
    def _mock_cmds(
        cmd: str,
        params: list[dict[str, Any]],
        results: list[dict[str, Any]],
        token: str = "fake-token",  # noqa: S107
        method: str = "POST",
    ):
        httpx_mock.add_response(
            url=f"https://example.com/cgi-bin/api.cgi?cmd={cmd}&token={token}",
            method=method,
            match_json=[
                {
                    "cmd": cmd,
                    "action": 0,
                    "param": param,
                }
                for param in params
            ],
            json=[
                {
                    "cmd": cmd,
                    "code": 0,
                    "value": result,
                }
                for result in results
            ],
        )

    return _mock_cmds


@pytest.mark.asyncio
async def test_reolink_nvr_interface(mock_cmd: MockCmd, mock_cmds: MockCmds):
    mock_cmd(
        cmd="Login",
        param={"User": {"userName": "admin", "password": "password"}},
        result={"Token": {"leaseTime": 3600, "name": "fake-token"}},
        token="null",  # noqa: S106
    )
    mock_cmd(
        cmd="Logout",
        result={"Token": {"name": "fake-token"}},
    )
    fake_channels = [
        "fake_camera_1",
        "",
        "",
        "",
        "",
        "fake_camera_6",
        "",
        "",
        "",
        "",
        "fake_camera_11",
        "",
        "",
        "",
        "",
        "fake_camera_16",
    ]
    mock_cmd(
        cmd="GetChannelStatus",
        result={
            "count": len(fake_channels),
            "status": [
                {
                    "channel": idx,
                    "name": channel,
                    "online": 1 if len(channel) > 0 else 0,
                    "uid": f"fake-uid-{idx}",
                    "sleep": 0,
                }
                for idx, channel in enumerate(fake_channels)
            ],
        },
    )
    mock_cmds(
        cmd="GetEnc",
        params=[
            {
                "channel": idx,
            }
            for idx, channel in enumerate(fake_channels)
            if channel
        ],
        results=[
            {
                "Enc": {
                    "audio": 1,
                    "channel": idx,
                    "mainStream": {
                        "bitRate": 6144,
                        "frameRate": 25,
                        "gop": 2,
                        "height": 2160,
                        "profile": "High",
                        "size": "3840*2160",
                        "vType": "h265",
                        "width": 3840,
                    },
                    "subStream": {
                        "bitRate": 256,
                        "frameRate": 10,
                        "gop": 4,
                        "height": 360,
                        "profile": "High",
                        "size": "640*360",
                        "vType": "h264",
                        "width": 640,
                    },
                },
            }
            for idx, channel in enumerate(fake_channels)
            if channel
        ],
    )

    config = ReolinkNvrInterfaceConfig(
        address="example.com",
        use_ssl=True,
        username="admin",
        password=SecretStr("password"),
    )
    iface = ReolinkNvrInterface(config)

    await iface.start()

    res = await iface.get_token()
    assert res == "fake-token"

    channels = await iface.get_channels()
    assert isinstance(channels, list)
    assert len(channels) == 4

    await iface.stop()
