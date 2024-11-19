from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Literal

from pydantic import SecretStr

from .http import (
    HttpBaseInterface,
    HttpBaseInterfaceConfig,
    RequestOptions,
)

if TYPE_CHECKING:
    from tag_sensor.camera import Camera


class HomeAssistantInterfaceConfig(HttpBaseInterfaceConfig):
    provider: Literal["homeassistant"] = "homeassistant"

    server: str = os.getenv("HASS_SERVER", "http://homeassistant.local:8123")
    token: SecretStr = SecretStr(os.getenv("HASS_TOKEN", ""))


@dataclass
class HomeAssistantInterface(HttpBaseInterface[HomeAssistantInterfaceConfig]):
    def http_client_options(self):
        token = self.config.token.get_secret_value()
        return {
            "base_url": self.config.server,
            "headers": {"authorization": "Bearer " + token},
        }

    async def get_frame_request(self, camera: Camera):
        _id = camera.config.entity_id or f"camera.{camera.config.id}"
        res = await self.client.get(f"/api/states/{_id}")
        data = res.json()
        return RequestOptions(url=data["attributes"]["entity_picture"])
