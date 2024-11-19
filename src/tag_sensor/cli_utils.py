from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from functools import partial, wraps
import inspect
import json
from typing import Any

import asyncer
from rich.pretty import pprint
from typer import Typer
import yaml


class App(Typer):  # pragma: no cover
    def __init__(self, **kwargs):
        args = {**kwargs}
        args.setdefault("no_args_is_help", True)
        args.setdefault("rich_markup_mode", "rich")
        args.setdefault("pretty_exceptions_short", True)
        args.setdefault("pretty_exceptions_enable", False)
        super().__init__(**args)

    def wrap_callback(self, decorator, f):
        if inspect.iscoroutinefunction(f):

            @wraps(f)
            def runner(*args, **kwargs):
                return asyncer.runnify(f)(*args, **kwargs)

            decorator(runner)
            return f

        decorator(f)
        return f

    def wrap_command(self, decorator, f):
        def wrap(fn):
            decorator(fn)
            return f

        if inspect.iscoroutinefunction(f):

            @wraps(f)
            def runner1(*args, **kwargs):
                return asyncer.runnify(f)(*args, **kwargs)

            return wrap(runner1)

        if inspect.isgeneratorfunction(f):

            @wraps(f)
            def runner2(*args, **kwargs):
                return list(f(*args, **kwargs))

            return wrap(runner2)

        if inspect.isasyncgenfunction(f):

            @wraps(f)
            async def _runner3(*args, **kwargs):
                results = []
                async for result in f(*args, **kwargs):
                    results.append(result)
                return results

            @wraps(f)
            def runner3(*args, **kwargs):
                return asyncer.runnify(_runner3)(*args, **kwargs)

            return wrap(runner3)

        return wrap(f)

    def callback(self, *args, **kwargs):
        decorator = super().callback(*args, **kwargs)
        return partial(self.wrap_callback, decorator)

    def command(
        self,
        *args,
        # model: type[Model] | None = None,
        **kwargs,
    ):
        decorator = super().command(*args, **kwargs)
        return partial(self.wrap_command, decorator)

    def pprint(self, data: Any):  # pragma: no cover
        pprint(data)


class Format(str, Enum):
    JSON = "json"
    JSONL = "jsonl"
    PRETTY = "pretty"
    YAML = "yaml"
    YAMLS = "yamls"


def jsonl_dump_item(data: Any):  # pragma: no cover
    return json.dumps(data) + "\n"


class Formatters:  # pragma: no cover
    def json(self, data: Any):
        print(json.dumps(data))  # noqa: T201

    def jsonl_one(self, data: Any):
        print(jsonl_dump_item(data))  # noqa: T201

    def pretty(self, data: Any):
        pprint(data)

    def pretty_one(self, data: Any):
        pprint(data)

    def yaml(self, data: Any):
        print(yaml.dump(data, explicit_start=True))  # noqa: T201

    def yamls_one(self, data: Any):
        print(yaml.dump_all(data, explicit_start=True).strip())  # noqa: T201


formatters = Formatters()


def format_output(fmt: Format, data: Any):  # pragma: no cover
    if data is None:
        return
    one_fn = getattr(formatters, f"{fmt.value}_one", None)

    if isinstance(data, Sequence):
        seq_fn = getattr(formatters, f"{fmt.value}_seq", None)
        if callable(seq_fn):
            seq_fn(data)
            return
        if one_fn:
            for item in data:
                one_fn(item)
            return
    elif callable(one_fn):
        one_fn(data)
        return

    fn = getattr(formatters, fmt.value)
    if callable(fn):
        fn(data)
        return

    print("Unable to locate formatter")  # noqa: T201
    pprint(data)
