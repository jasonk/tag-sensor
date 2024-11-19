from __future__ import annotations

from asyncio import sleep
from dataclasses import dataclass, field
from functools import cached_property
from time import time
from typing import TYPE_CHECKING

import cv2
import structlog

from tag_sensor.emitter import emit as _emit
from tag_sensor.frame import Frame

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cv2.typing import MatLike

    from .calibrator import Calibrator
    from .config import CalibrationConfig

logger = structlog.get_logger()


@dataclass
class Capture:
    original_frame: Frame

    config: CalibrationConfig

    timestamp: int = field(
        init=False,
        default_factory=lambda: int(time()),
    )

    charuco_corners: MatLike
    charuco_ids: MatLike
    marker_corners: Sequence[MatLike]
    marker_ids: MatLike
    corners: MatLike

    @property
    def rows(self):
        return self.config.rows

    @property
    def cols(self):
        return self.config.columns

    imsize: tuple[int, int]

    @cached_property
    def annotated_frame(self) -> Frame:
        return self.original_frame.transform(self._annotate_frame)

    def _annotate_frame(self, image: MatLike) -> MatLike:
        cv2.aruco.drawDetectedCornersCharuco(
            image,
            self.corners,
            self.charuco_ids,
        )
        cv2.drawChessboardCorners(
            image,
            (self.rows, self.cols),
            self.corners,
            True,
        )
        return image

    @classmethod
    async def capture(cls, calibrator: Calibrator):
        attempt = 0

        def emit(event: str, **kwargs):
            _emit(f"capture:{event}", **kwargs)

        def fail(msg: str):  # pragma: no cover
            emit("failed", message=msg)

        emit("started")
        manager = calibrator.manager
        camera = calibrator.camera
        config = calibrator.config
        board_detector = config.board_detector

        while attempt < config.attempts:
            await sleep(config.delay)
            attempt += 1
            emit("attempt", attempt=attempt)
            original_frame = await manager.get_frame(camera)
            if not original_frame:  # pragma: no cover
                fail("no frame captured")
                continue
            input_frame = original_frame.grayscale()

            (
                charuco_corners,
                charuco_ids,
                marker_corners,
                marker_ids,
            ) = board_detector.detectBoard(input_frame.contents)
            if charuco_ids is None:  # pragma: no cover
                fail("no charuco_ids detected")
                continue

            have = len(charuco_ids)
            want = config.markers
            if have <= want:  # pragma: no cover
                fail(f"only {have} charuco ids detected ({want} needed)")
                continue

            corners = cv2.cornerSubPix(
                input_frame.contents,
                charuco_corners,
                (11, 11),  # TODO - Does this need to be configurable?
                (-1, -1),  # TODO - Does this need to be configurable?
                (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    100,
                    0.00001,  # TODO - Does this need to be configurable?
                ),
            )
            capture = cls(
                config=config,
                original_frame=original_frame,
                charuco_corners=charuco_corners,
                charuco_ids=charuco_ids,
                marker_corners=marker_corners,
                marker_ids=marker_ids,
                corners=corners,
                imsize=input_frame.contents.shape[::-1],
            )
            emit("good")
            return capture
        return None
