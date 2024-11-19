from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    TypedDict,
    TypeVar,
)

from httpx import URL, AsyncClient, Response, Timeout
from pydantic import BaseModel, SecretStr
import structlog

from tag_sensor.utils import fill_templates

from .base import BaseInterface, BaseInterfaceConfig

if TYPE_CHECKING:
    from httpx._types import (
        AuthTypes,
        HeaderTypes,
        QueryParamTypes,
        TimeoutTypes,
    )

    from tag_sensor.camera import Camera

logger = structlog.get_logger()


class HttpBaseInterfaceConfig(BaseInterfaceConfig):
    verify_ssl: bool = True
    follow_redirects: bool = True
    timeout: float = 10


ConfigT = TypeVar("ConfigT", bound=HttpBaseInterfaceConfig)


class HttpxRequestKwargs(TypedDict, total=False):
    params: QueryParamTypes
    headers: HeaderTypes
    auth: AuthTypes
    timeout: TimeoutTypes
    follow_redirects: bool
    json: Any


@dataclass(kw_only=True)
class RequestOptions:
    url: str | URL
    post: bool = False

    username: str | None = None
    password: str | SecretStr | None = None
    timeout: float | None = None

    params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    follow_redirects: bool = False
    json: Any | None = None

    def __post_init__(self):
        if self.json:
            self.post = True

    def get_httpx_kwargs(self) -> HttpxRequestKwargs:
        kwargs = HttpxRequestKwargs(
            params=self.params,
            headers=self.headers,
            follow_redirects=self.follow_redirects,
            json=self.json,
        )

        if self.username and self.password:
            username = self.username
            password = self.password
            if isinstance(password, SecretStr):
                password = password.get_secret_value()
            kwargs["auth"] = (username, password)
        if self.timeout:
            kwargs["timeout"] = Timeout(self.timeout)
        return kwargs

    @property
    def method(self) -> Literal["GET", "POST"]:
        return "POST" if self.post else "GET"

    def get_request(self):
        return self.method, self.url, self.get_httpx_kwargs()


@dataclass
class HttpBaseInterface(Generic[ConfigT], BaseInterface[ConfigT]):
    def http_client_options(self) -> dict[str, Any]:
        return {
            "verify": self.config.verify_ssl,
            "follow_redirects": self.config.follow_redirects,
            "timeout": self.config.timeout,
        }

    @abstractmethod
    async def get_frame_request(
        self,
        camera: Camera,
    ) -> RequestOptions | None: ...

    @cached_property
    def client(self) -> AsyncClient:
        return AsyncClient(**self.http_client_options())  # nosec

    async def do_request(self, req: RequestOptions):
        return await self.client.request(
            req.method,
            req.url,
            **req.get_httpx_kwargs(),
        )

    async def get_frame(self, camera: Camera):
        req = await self.get_frame_request(camera)
        if req is None:
            return None
        res = await self.do_request(req)
        return await self.frame_from_response(res, camera)

    async def frame_from_response(self, res: Response, camera: Camera):
        if not res.headers.get("content-type").startswith("image/"):
            logger.error(
                "Response is not image",
                headers=res.headers,
                text=res.text,
                camera=camera.id,
            )
            return None
        # pylint: disable-next=import-outside-toplevel
        from tag_sensor.frame import Frame

        return Frame.from_bytes(res.read())


class CameraRequestError(Exception):
    def __init__(self, camera_id: str):
        super().__init__(f"Request failed: {camera_id}")


class HttpInterfaceTemplateConfig(BaseModel):
    url: str
    post: bool = False

    username: str | None = None
    password: SecretStr | None = None
    timeout: float | None = None

    params: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    follow_redirects: bool | None = None
    # json: Any = None


class HttpInterfaceConfig(HttpBaseInterfaceConfig):
    provider: Literal["http"] = "http"
    template: HttpInterfaceTemplateConfig
    headers: dict[str, str] = {}
    params: dict[str, str] = {}


class HttpInterface(HttpBaseInterface[HttpInterfaceConfig]):
    async def get_frame_request(self, camera: Camera):
        if not self.config.template:
            logger.error("template is not set", camera=camera.id)
            return None
        conf = camera.config.model_dump()
        data = fill_templates(self.config.template, conf)
        return RequestOptions(**data)
