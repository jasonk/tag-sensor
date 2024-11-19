from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass, replace
from io import BytesIO
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy

if TYPE_CHECKING:
    from collections.abc import Callable

    from cv2.typing import MatLike

IS_ITERM = os.environ.get("TERM_PROGRAM", "") == "iTerm.app"


class EmptyFrameError(ValueError):  # pragma: no cover
    def __init__(self):
        super().__init__("Frame has no contents")


@dataclass(frozen=True, eq=True)
class Frame:
    contents: MatLike
    is_grayscale: bool = False

    def __post_init__(self):  # pragma: no cover
        if self.contents is None:
            raise EmptyFrameError

    @classmethod
    def from_bytes(cls, raw_data: bytes) -> Frame:  # pragma: no cover
        content = BytesIO(raw_data)
        data = numpy.frombuffer(content.read(), numpy.uint8)
        contents = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return Frame(contents=contents)

    @classmethod
    def from_file(cls, filename: str) -> Frame | None:
        file = Path(filename)
        if not file.is_file():
            return None  # pragma: no cover
        contents = cv2.imread(str(file), cv2.IMREAD_COLOR)
        return Frame(contents=contents)

    def copy(self, **kwargs) -> Frame:
        if "contents" not in kwargs:
            kwargs["contents"] = self.contents.copy()
        return replace(self, **kwargs)

    def transform(
        self,
        fn: Callable[[MatLike], MatLike],
        *args: Any,
        **kwargs,
    ) -> Frame:
        contents = fn(self.contents.copy(), *args)
        return replace(self, contents=contents, **kwargs)

    def grayscale(self):
        def _grayscale(image: MatLike) -> MatLike:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return self.transform(_grayscale, is_grayscale=True)

    def to_image(self, image_format: str = "png") -> bytes:
        """
        Convert the frame to an image file format.

        Supported formats are those supported by the OpenCV library in
        use. In general that means these should always work:

            * Portable Network Graphics - *.png (default)
            * Windows bitmaps - *.bmp, *.dib
            * Portable image format - *.pbm, *.pgm, *.ppm *.pxm, *.pnm
            * Sun rasters - *.sr, *.ras
            * Radiance HDR - *.hdr, *.pic

        These may work, depending on the build of OpenCV in use:
            * JPEG files - *.jpeg, *.jpg, *.jpe
            * JPEG 2000 files - *.jp2
            * WebP - *.webp
            * TIFF files - *.tiff, *.tif
            * OpenEXR Image files - *.exr
        """
        fmt = "." + image_format.lower().lstrip(".")
        is_success, buffer = cv2.imencode(fmt, self.contents)
        if not is_success:
            raise AssertionError
        io_buf = BytesIO(buffer)  # type: ignore
        return io_buf.getvalue()

    def to_png(self) -> bytes:
        return self.to_image("png")

    def display(self) -> None:
        if IS_ITERM:  # pragma: no cover
            image = self.to_png()
            parts: list[str] = [
                "1337;File=inline=1",
                "type=image/png",
                "preserveAspectRatio=1",
                "width=100%",
                f"size={len(image)}",
                # f'name={b64encode(label.encode()).decode()}',
            ]

            print("\033]" + ";".join(parts), end=":")  # noqa: T201
            print(b64encode(image).decode(), end="")  # noqa: T201
            print("\a")  # noqa: T201

    def save(self, filename: str | Path, image_format: str | None = None):
        file = Path(filename)
        if image_format is None:
            image_format = file.suffix.lstrip(".")
        if not image_format:
            image_format = "png"
        file = file.with_suffix("." + image_format)
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("wb") as fh:
            fh.write(self.to_image(image_format))
        return file
