from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass
class BaseClass:
    def __rich_repr__(self):
        for f in fields(self):
            if f.repr is False:
                continue
            yield f.name, getattr(self, f.name, None), f.default
