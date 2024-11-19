from __future__ import annotations

from string import Template
from typing import TYPE_CHECKING, Any

import cv2
import numpy
import structlog

if TYPE_CHECKING:
    from cv2.typing import MatLike

logger = structlog.get_logger()

COLORS = {
    "white": (255, 255, 255),
    "silver": (192, 192, 192),
    "gray": (128, 128, 128),
    "black": (0, 0, 0),
    "red": (0, 0, 255),
    "maroon": (0, 0, 128),
    "yellow": (0, 255, 255),
    "olive": (0, 128, 128),
    "lime": (0, 255, 0),
    "green": (0, 128, 0),
    "aqua": (255, 255, 0),
    "teal": (128, 128, 0),
    "blue": (255, 0, 0),
    "navy": (128, 0, 0),
    "fuchsia": (255, 0, 255),
    "purple": (128, 0, 128),
}


def parse_color(color: str) -> tuple[int, int, int]:
    if color in COLORS:
        return COLORS[color]
    if color.startswith("#"):
        color = color.lstrip("#").strip()
        return (
            int(color[4:6], 16),
            int(color[2:4], 16),
            int(color[0:2], 16),
        )
    if color.startswith("RGB(") and color.endswith(")"):
        parts = color[4:-1].split(",")
        if len(parts) == 3:  # noqa: PLR2004
            return (int(parts[0]), int(parts[1]), int(parts[2]))
    msg = f"Invalid color: {color}"
    raise ValueError(msg)


def add_text_to_image(  # noqa: PLR0913
    image: MatLike,
    text: str,
    origin: tuple[int, int] = (0, 0),
    color: tuple[int, int, int] | str = (0, 0, 0),
    outline: tuple[int, int, int] | str = (255, 255, 255),
    scale: float = 0.5,
    thickness: int = 1,
    font: str = "FONT_HERSHEY_SIMPLEX",
    line_spacing: float = 1.5,
    line_type: str = "LINE_AA",
):
    pos = numpy.array(origin, dtype=float)
    _font_face = getattr(cv2, font, None)
    if _font_face is None:  # pragma: no cover
        logger.error("Invalid font specified", font=font)
        _font_face = cv2.FONT_HERSHEY_SIMPLEX
    _line_type = getattr(cv2, line_type, None)
    if _line_type is None:  # pragma: no cover
        logger.error("Invalid line type specified", line_type=line_type)
        _line_type = cv2.LINE_AA

    color = parse_color(color) if isinstance(color, str) else color
    outline = parse_color(outline) if isinstance(outline, str) else outline

    for line in text.splitlines():
        (_, h), _ = cv2.getTextSize(
            text=line,
            fontFace=_font_face,
            fontScale=scale,
            thickness=thickness,
        )

        pos += [0, h]
        org = tuple(pos.astype(int))

        if outline is not None:  # pragma: no cover
            cv2.putText(
                image,
                text=line,
                org=org,
                fontFace=_font_face,
                fontScale=scale,
                lineType=_line_type,
                color=outline,
                thickness=thickness * 3,
            )
        cv2.putText(
            image,
            text=line,
            org=org,
            fontFace=_font_face,
            fontScale=scale,
            lineType=_line_type,
            color=color,
            thickness=thickness,
        )

        pos += [0, h * line_spacing]


def apply_defaults(data: dict[str, Any], defaults: dict[str, Any]):
    for key, value in defaults.items():
        if isinstance(value, dict):
            data.setdefault(key, {})
            apply_defaults(data[key], value)
        else:
            data.setdefault(key, value)


def fill_template(
    template: str,
    data: dict[str, Any],
) -> str:
    tmpl = Template(template)
    return tmpl.substitute(data)


def fill_templates(
    templates: Any,
    data: Any,
) -> Any:
    if isinstance(templates, str):
        return fill_template(templates, data)
    if isinstance(templates, list):
        return [fill_templates(t, data) for t in templates]
    if isinstance(templates, dict):
        return {
            fill_template(k, data): fill_templates(v, data)
            for k, v in templates.items()
        }
    return templates


class NotFoundError(Exception):
    pass
