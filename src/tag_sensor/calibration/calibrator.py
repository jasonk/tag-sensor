from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import cv2
import structlog

from .capture import Capture
from .record import CalibrationRecord

if TYPE_CHECKING:
    from tag_sensor.camera import Camera
    from tag_sensor.manager import Manager

    from .config import CalibrationConfig

logger = structlog.get_logger()


@dataclass
class Calibrator:
    camera: Camera
    manager: Manager

    captures: list[Capture] = field(default_factory=list, init=False)
    need: int = field(default=0, init=False)

    def __post_init__(self):
        self.need = self.config.samples

    @property
    def config(self) -> CalibrationConfig:
        return self.camera.config.calibration

    async def calibrate(self):
        calibration = await self.collect()
        self.camera.update_calibration(calibration)
        return calibration

    def msg(self, msg: str):
        logger.info(msg)
        self.camera.set_message(msg)

    async def capture_frames(self):
        self.msg("Beginning calibration image captures")

        did = 0
        while self.need > 0:
            self.msg(f"Capturing frame {did+1} of {self.config.samples}")

            if capture := await Capture.capture(self):
                yield capture
                self.camera.emit_frame("capture", capture.annotated_frame)
                did += 1
                self.need -= 1
            else:  # pragma: no cover
                self.msg("Capture failed")

    async def collect(self) -> CalibrationRecord | None:
        captures: list[Capture] = [f async for f in self.capture_frames()]

        res, matrix, distortion, *_ = cv2.aruco.calibrateCameraCharuco(
            charucoCorners=[c.charuco_corners for c in captures],
            charucoIds=[c.charuco_ids for c in captures],
            board=self.config.board,
            imageSize=captures[0].imsize,
            cameraMatrix=None,  # type: ignore
            distCoeffs=None,  # type: ignore
            # rvecs, tvecs, flags, criteria
        )
        if not res:  # pragma: no cover
            logger.debug("calibrateCameraCharuco failed")
            return None

        return CalibrationRecord(
            matrix,
            distortion,
            config=self.config,
        )
