from __future__ import annotations

from collections import defaultdict
from inspect import Parameter, signature
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable

logger = structlog.get_logger()

listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)


def add_event_listener(event: str, listener: Callable[..., None]) -> None:
    listeners[event].append(listener)


def emit(event: str, **kwargs: Any):
    for listener in listeners.get(event, []) + listeners.get("*", []):
        safe_call(listener, event=event, **kwargs)


def safe_call(
    func: Callable[..., Any],
    # *args: Any,
    **kwargs: Any,
) -> None:
    wants_args: list[Any] = []
    wants_kwargs: dict[str, Any] = {}

    params = signature(func).parameters

    if any(p.kind == Parameter.VAR_KEYWORD for p in params.values()):
        wants_kwargs = kwargs
    else:
        for key, value in kwargs.items():
            kwparam = params.get(key)
            if kwparam is None:
                continue
            if kwparam.kind in (
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.KEYWORD_ONLY,
            ):
                wants_kwargs[key] = value

    try:
        func(*wants_args, **wants_kwargs)
    except TypeError:
        logger.exception("Error in safe_call", function=func)
