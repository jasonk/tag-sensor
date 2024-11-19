from __future__ import annotations

import json

from httpx import Response


def is_json(res: Response) -> bool:
    ct = res.headers.get("content-type")
    if ct.endswith("/json"):
        return True
    if ct == "text/html":
        try:
            json.loads(res.text)
        except json.JSONDecodeError:
            return False
        else:
            return True
    return False


def is_error(res: Response) -> str | None:
    if not is_json(res):
        return None
    try:
        data = json.loads(res.text)
        if isinstance(data, list):
            data = data[0]
        if isinstance(data, dict):
            error = data.get("error")
            if error:
                return error["detail"]
            return None
    except json.JSONDecodeError:
        return None
    return None
