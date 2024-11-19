from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Any, Literal

import structlog

from tag_sensor.interfaces.http import RequestOptions

from .base import ReolinkBaseInterface, ReolinkBaseInterfaceConfig
from .channels import ReolinkNvrChannel, ReolinkNvrStream

if TYPE_CHECKING:
    from tag_sensor.camera import Camera

logger = structlog.get_logger()


class ReolinkNvrInterfaceConfig(ReolinkBaseInterfaceConfig):
    provider: Literal["reolink-nvr"] = "reolink-nvr"
    address: str


@dataclass
class ReolinkNvrInterface(ReolinkBaseInterface[ReolinkNvrInterfaceConfig]):
    def http_client_options(self) -> dict[str, Any]:
        url = "".join(
            [
                "https://" if self.config.use_ssl else "http://",
                self.config.address,
            ],
        )
        return super().http_client_options() | {"base_url": url}

    async def get_camera_url(self, camera: Camera):
        channel = await self.find_channel(camera)
        if not channel:
            logger.error("Camera not found", camera=camera.id)
            return None
        url = await super().get_camera_url(camera)
        if not url:
            return None
        return url.copy_set_param("channel", str(channel.channel))

    _channels: list[ReolinkNvrChannel] | None = None

    async def get_channels(self) -> list[ReolinkNvrChannel]:
        if self._channels:
            return self._channels
        channels: list[ReolinkNvrChannel] = [
            channel async for channel in self.get_channel_data()
        ]
        self._channels = channels
        return channels

    async def get_channel_data(
        self,
    ) -> AsyncGenerator[ReolinkNvrChannel, None]:
        channels = await self.do_cmd("GetChannelStatus", pluck="status")
        enc_info = await self.do_cmds(
            "GetEnc",
            *({"channel": c["channel"]} for c in channels if c["online"]),
            pluck="Enc",
        )
        for enc in enc_info:
            channel = enc.get("channel")
            streams: list[ReolinkNvrStream] = []
            for key, value in enc.items():
                if key.endswith("Stream"):
                    streams.append(
                        ReolinkNvrStream(
                            name=key,
                            height=value["height"],
                            width=value["width"],
                        ),
                    )
            yield ReolinkNvrChannel(
                **channels[channel],
                streams=streams,
            )

    async def find_channel(self, camera: Camera):
        for channel in await self.get_channels():
            if channel.matches(camera):
                return channel
        return None

    async def get_frame_request(self, camera: Camera):
        channel = await self.find_channel(camera)
        if not channel:
            logger.error("Camera not found", camera=camera.id)
            return None

        params: dict[str, str] = {
            "cmd": "Snap",
            "channel": str(channel.channel),
            "rs": str(time.time()),
        }
        if camera.config.stream:
            if stream := channel.stream(camera.config.stream):
                params["height"] = str(stream.height)
                params["width"] = str(stream.width)
            else:
                logger.error("Stream not found", stream=camera.config.stream)

        if token := await self.get_token():
            params.update({"token": token})
        else:
            params.update(
                {
                    "userName": self.config.username,
                    "password": self.config.password.get_secret_value(),
                },
            )

        return RequestOptions(
            url="/cgi-bin/api.cgi",
            params=params,
        )
