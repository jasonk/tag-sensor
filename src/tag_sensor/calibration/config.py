from __future__ import annotations

from functools import cached_property
from typing import Any

import cv2
from cv2.aruco import CharucoBoard

from tag_sensor.family import FamilyGroup, get_family
from tag_sensor.frame import Frame
from tag_sensor.model import Model


class CalibrationConfig(Model):
    rows: int = 9
    """Number of rows in the calibration grid."""
    columns: int = 6
    """Number of columns in the calibration grid."""
    square_size: float = 45.0
    """Size of the chessboard squares in the calibration grid."""
    marker_size: float = 25.0
    """Size of the markers in the calibration grid."""
    samples: int = 20
    """Number of samples to take for calibration."""
    delay: float = 3
    """Delay between samples for calibration."""
    attempts: float = 20
    """Maximum number of attempts to capture a frame for calibration."""
    markers: int = 25
    """Minimum number of detected ids to consider a frame for calibration."""
    family: FamilyGroup = "4X4"

    def get_family(self):
        return get_family(self.family)

    def to_data(self):
        return self.model_dump(
            include={
                "rows",
                "columns",
                "square_size",
                "marker_size",
                "samples",
                "delay",
                "attempts",
                "markers",
                "family",
            },
        )

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        return cls(**data)

    @cached_property
    def board(self) -> CharucoBoard:
        return CharucoBoard(
            (self.rows, self.columns),
            self.square_size / 1000,
            self.marker_size / 1000,
            self.get_family().dictionary(),
        )

    @cached_property
    def board_detector(self):
        return cv2.aruco.CharucoDetector(self.board)

    def make_calibration_board(
        self,
        width: float = 11,  # TODO - This is inches
        dpi: int = 300,
    ) -> Frame:
        col_pixels = int(width * dpi)
        ratio = self.columns / self.rows
        row_pixels = int(col_pixels / ratio)

        image = self.board.generateImage((row_pixels, col_pixels))
        return Frame(contents=image)
