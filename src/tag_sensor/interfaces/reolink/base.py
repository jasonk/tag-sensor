from __future__ import annotations

from dataclasses import dataclass, field
import time
from asyncio import CancelledError
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from httpx import URL, HTTPError
from pydantic import SecretStr
import structlog

from tag_sensor.interfaces.http import (
    HttpBaseInterface,
    HttpBaseInterfaceConfig,
    RequestOptions,
)
from tag_sensor.server.utils import shutting_down

from .utils import is_error

if TYPE_CHECKING:
    from tag_sensor.camera import Camera

logger = structlog.get_logger()


class ReolinkBaseInterfaceConfig(HttpBaseInterfaceConfig):
    address: str | None = None
    username: str = "admin"
    password: SecretStr = SecretStr("")
    use_ssl: bool = False
    verify_ssl: bool = False


ConfigT = TypeVar("ConfigT", bound=ReolinkBaseInterfaceConfig)


@dataclass
class ReolinkBaseInterface(Generic[ConfigT], HttpBaseInterface[ConfigT]):
    token: str | None = field(default=None, repr=False)

    async def get_camera_url(self, camera: Camera) -> URL | None:
        return URL(
            scheme="https" if self.config.use_ssl else "http",
            host=self.config.address or camera.config.address or camera.id,
            path="/cgi-bin/api.cgi",
        )

    async def get_frame_request(self, camera: Camera):
        url = await self.get_camera_url(camera)
        if url is None:
            logger.error("No URL for camera", camera=camera.id)
            return None

        req = RequestOptions(
            url=url,
            params={
                "cmd": "Snap",
                "channel": "0",
                "rs": str(time.time()),
            },
        )

        if self.token:
            req.params.update({"token": self.token})
        else:
            username = camera.config.username or self.config.username
            password = camera.config.password or self.config.password
            if isinstance(password, SecretStr):
                password = password.get_secret_value()
            req.params.update({"user": username, "password": password})

        return req

    async def do_request(self, req: RequestOptions):
        args = req.method, req.url
        kwargs = req.get_httpx_kwargs()

        res = await self.client.request(*args, **kwargs)
        if error := is_error(res):  # noqa: SIM102
            if error.lower() == "please login first":
                await self.login()
                return await self.client.request(*args, **kwargs)
        return res

    async def _do_req(
        self,
        cmd: str,
        json: list[dict[str, Any]],
    ):
        if not self.token:
            await self.login()
        res = await self.do_request(
            RequestOptions(
                post=True,
                url="/cgi-bin/api.cgi",
                params={"cmd": cmd, "token": self.token or "null"},
                json=json,
            ),
        )
        if error := is_error(res):
            if error.lower() == "please login first":
                await self.login()
                return await self._do_req(cmd, json)
            raise HTTPError(error)
        results: list[Any] = []
        for item in res.json():
            if item.get("code") != 0:
                logger.error(
                    "Error returned for command",
                    command=cmd,
                    item=item,
                )
            else:
                results.append(item["value"])
        return results

    async def do_cmd(
        self,
        cmd: str,
        action: Literal[0, 1] = 0,
        pluck: str | None = None,
        **param,
    ):
        json = [{"cmd": cmd, "action": action, "param": param}]
        res = await self._do_req(cmd, json)
        if pluck:
            return self.pluck(pluck, res[0])
        return res[0]

    async def do_cmds(
        self,
        cmd: str,
        *params: dict[str, Any],
        action: Literal[0, 1] = 0,
        pluck: str | None = None,
    ):
        json = [{"cmd": cmd, "action": action, "param": p} for p in params]
        res = await self._do_req(cmd, json)
        if pluck:
            return [self.pluck(pluck, r) for r in res]
        return res

    async def login(self):
        if shutting_down.is_set():
            logger.debug("Skipping login due to shutdown")
            raise CancelledError
        logger.debug("Logging in")
        username = self.config.username
        password = self.config.password.get_secret_value()
        res = await self.do_request(
            RequestOptions(
                post=True,
                url="/cgi-bin/api.cgi",
                params={"cmd": "Login", "token": "null"},
                json=[
                    {
                        "cmd": "Login",
                        "action": 0,
                        "param": {
                            "User": {
                                "userName": username,
                                "password": password,
                            },
                        },
                    },
                ],
            ),
        )
        if error := is_error(res):
            raise HTTPError(error)
        result = res.json()[0]
        self.token = result["value"]["Token"]["name"]

    async def logout(self):
        logger.debug("Logging out")
        if not self.token:
            return
        await self.do_cmd("Logout")

    async def stop(self):
        await self.logout()

    async def get_token(self):
        if self.token:
            return self.token
        await self.login()
        return self.token

    def pluck(self, path: str, data: dict[str, Any]) -> Any:
        for key in path.split("."):
            val = data.get(key)
            if val is None:
                return None  # pragma: no cover
            data = val
        return data
