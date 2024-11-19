from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from .base import BaseInterface, BaseInterfaceConfig
from .dummy import DummyInterface, DummyInterfaceConfig
from .homeassistant import (
    HomeAssistantInterface,
    HomeAssistantInterfaceConfig,
)
from .http import (
    HttpInterface,
    HttpInterfaceConfig,
    HttpInterfaceTemplateConfig,
)
from .reolink import (
    ReolinkCameraInterface,
    ReolinkCameraInterfaceConfig,
    ReolinkNvrInterface,
    ReolinkNvrInterfaceConfig,
)
from .script import ScriptInterface, ScriptInterfaceConfig

Interface = Annotated[
    Union[
        DummyInterface,
        HttpInterface,
        HomeAssistantInterface,
        ReolinkCameraInterface,
        ReolinkNvrInterface,
        ScriptInterface,
    ],
    Field(discriminator="provider"),
]
InterfaceConfig = Annotated[
    Union[
        DummyInterfaceConfig,
        HttpInterfaceConfig,
        HomeAssistantInterfaceConfig,
        ReolinkCameraInterfaceConfig,
        ReolinkNvrInterfaceConfig,
        ScriptInterfaceConfig,
    ],
    Field(discriminator="provider"),
]


class ProviderNotFoundError(ValueError):  # pragma: no cover
    def __init__(self, provider: str) -> None:
        super().__init__(f"Unknown provider: {provider}")


def make_interface(config: InterfaceConfig) -> Interface:
    provider = config.provider
    data = config.model_dump()
    if provider == "dummy":
        return DummyInterface(DummyInterfaceConfig(**data))
    if provider == "http":
        return HttpInterface(HttpInterfaceConfig(**data))
    if provider == "homeassistant":
        return HomeAssistantInterface(HomeAssistantInterfaceConfig(**data))
    if provider == "script":
        return ScriptInterface(ScriptInterfaceConfig(**data))
    if provider == "reolink":
        return ReolinkCameraInterface(ReolinkCameraInterfaceConfig(**data))
    if provider == "reolink-nvr":
        return ReolinkNvrInterface(ReolinkNvrInterfaceConfig(**data))
    raise ProviderNotFoundError(provider)  # pragma: no cover


__all__ = (
    "BaseInterface",
    "BaseInterfaceConfig",
    "DummyInterface",
    "DummyInterfaceConfig",
    "HomeAssistantInterface",
    "HomeAssistantInterfaceConfig",
    "HttpInterface",
    "HttpInterfaceConfig",
    "HttpInterfaceTemplateConfig",
    "Interface",
    "InterfaceConfig",
    "ReolinkCameraInterface",
    "ReolinkCameraInterfaceConfig",
    "ReolinkNvrInterface",
    "ReolinkNvrInterfaceConfig",
    "ScriptInterface",
    "ScriptInterfaceConfig",
)
