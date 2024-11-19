from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy
import yaml

from .config import CalibrationConfig

if TYPE_CHECKING:
    from cv2.typing import MatLike


@dataclass
class CalibrationRecord:
    matrix: MatLike
    distortion: MatLike
    # rotation: Any
    # translation: Any
    config: CalibrationConfig
    # mean_error: float

    #   def estimate_pose( self, frame: Frame ):
    #       gray = frame.grayscale()
    #       dim = gray.contents.shape[::-1]
    #       matrix, rot = cv2.getOptimalNewCameraMatrix(
    #           self.matrix, self.distortion, dim, 1, dim,
    #       )

    def to_data(self):
        return {
            "matrix": numpy.asarray(self.matrix).tolist(),
            "distortion": numpy.asarray(self.distortion).tolist(),
            # 'rotation': self.rotation.tolist(),
            # 'translation': self.translation.tolist(),
            "config": self.config.to_data(),
        }

    def save(self, file: Path):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(yaml.dump(self.to_data()))
        return file

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        return cls(
            matrix=numpy.array(data["matrix"]),
            distortion=numpy.array(data["distortion"]),
            # rotation = numpy.array( data['rotation'] ),
            # translation = numpy.array( data['translation'] ),
            config=CalibrationConfig.from_data(data["config"]),
        )

    @classmethod
    def load(cls, file: Path):
        if not file.is_file():
            return None
        return cls.from_data(yaml.safe_load(file.read_text()))
