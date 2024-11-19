from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
import math
from typing import TYPE_CHECKING, Any

import cv2
import numpy

from .frame import Frame
from .utils import add_text_to_image, parse_color

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cv2.typing import MatLike

    from .camera import Camera
    from .family import Family, FamilyGroup
    from .marker import Attrs, Marker

Integer = numpy.integer[Any]
Floating = numpy.floating[Any]
Points = numpy.ndarray[Any, numpy.dtype[Integer | Floating]]

FloatingPoints = numpy.ndarray[Any, numpy.dtype[Floating]]


@dataclass(kw_only=True)
class Detection:
    tag_id: int
    marker: Marker | None = field(default=None, repr=False)
    camera: Camera = field()
    family: Family = field()
    corners: Points = field()
    timestamp: datetime = field(default_factory=datetime.now)

    original_frame: Frame = field(repr=False)

    @property
    def edge_length(self):
        corners = self.corners.reshape((4, 2))
        return math.dist(corners[0], corners[1])

    @cached_property
    def pose(self):
        marker = self.marker
        calib = self.camera.calibration
        if not (marker and calib):
            return None  # pragma: no cover
        pose_points = marker.pose_points
        if pose_points is None:
            return None  # pragma: no cover
        _, rvec, tvec = cv2.solvePnP(
            pose_points,
            self.corners,
            calib.matrix,
            calib.distortion,
            None,
            None,
            False,
            cv2.SOLVEPNP_IPPE_SQUARE,
        )
        return rvec, tvec

    def warnings(self):
        if self.marker:
            if not self.marker.config.size:
                yield "Marker size not defined, cannot compute distance"
        else:
            yield "No marker associated, cannot compute distance"

        if not self.camera.calibration:
            yield "No camera calibration, cannot compute distance"

    @cached_property
    def rvec(self):
        if self.pose is None:
            return None
        return self.pose[0]

    @cached_property
    def tvec(self):
        if self.pose is None:
            return None
        return self.pose[1]

    @cached_property
    def raw_distance(self) -> float | None:
        tvec = self.tvec
        if tvec is None:
            return None
        return float(numpy.linalg.norm(tvec))

    @cached_property
    def distance(self) -> float | None:
        val = self.raw_distance
        if val is None:
            return None
        if self.marker:
            unit = self.marker.config.distance_unit
            if unit == "cm":
                val /= 10
            elif unit == "m":
                val /= 1000
            elif unit == "in":
                val /= 25.4
            elif unit == "ft":
                val /= 25.4 * 12
            decimals = self.marker.config.distance_decimals
            if isinstance(decimals, int):
                val = round(val, decimals)
        return val

    @cached_property
    def sort_distance(self) -> float | int:
        real = self.raw_distance
        if real is not None:
            return real
        return self.edge_length * 100000

    @property
    def attributes(self) -> Attrs:
        res: Attrs = {
            "camera": self.camera.config.id,
            "timestamp": self.timestamp.isoformat(),
            "tag_id": str(self.tag_id),
        }
        if self.marker and self.marker.config.name:
            res.update({"marker": self.marker.config.name})

        if self.raw_distance:
            res.update(
                {
                    "distance": self.distance,
                    "raw_distance": self.raw_distance,
                },
            )
        return res

    @cached_property
    def annotated_frame(self) -> Frame:
        return self.original_frame.transform(self._annotate_frame)

    def _annotate_frame(self, image: MatLike) -> MatLike:
        self.annotate_image_overlay_attributes(image)
        self.annotate_image_frame_axes(image)
        self.annotate_image_markers(image)
        return image

    def annotate_image_overlay_attributes(self, image: MatLike):
        overlay = self.camera.config.overlay

        # pylint: disable-next=too-many-return-statements
        def get_value(key: str) -> str | None:  # noqa: PLR0911
            if key == "camera":
                return self.camera.config.id
            if key == "timestamp":
                return self.timestamp.isoformat()
            if key == "tag_id":
                return f"#{self.tag_id}"
            if key == "edge_length":
                return f"{int(self.edge_length)} px"
            if key == "marker" and self.marker:
                return self.marker.config.name
            if key == "message":
                return self.camera.message
            if key == "distance" and self.distance:
                return str(self.distance)
            return None  # pragma: no cover

        lines: list[str] = []
        for key in overlay.attributes:
            if key == "":
                lines.append("")
                continue
            val = get_value(key)
            if val is None:
                continue  # pragma: no cover
            lines.append(f"{key}: {val}")

        add_text_to_image(
            image,
            "\n".join(lines),
            **overlay.model_dump(
                include={
                    "scale",
                    "thickness",
                    "font",
                    "line_spacing",
                    "line_type",
                    "color",
                    "outline",
                },
            ),
        )

    def annotate_image_markers(self, image: MatLike):
        overlay = self.camera.config.overlay

        if not overlay.marker:
            return  # pragma: no cover
        cv2.aruco.drawDetectedMarkers(
            image=image,
            corners=[self.corners],
            ids=numpy.array([self.tag_id]),
        )

    def annotate_image_frame_axes(self, image: MatLike):
        calib = self.camera.calibration
        if calib is None:
            return  # pragma: no cover
        marker = self.marker
        if marker is None:
            return  # pragma: no cover
        size = marker.config.size
        if not size:
            return  # pragma: no cover
        rvec = self.rvec
        tvec = self.tvec
        if rvec is None or tvec is None:
            return  # pragma: no cover
        cv2.drawFrameAxes(
            image,
            calib.matrix,
            calib.distortion,
            rvec,
            tvec,
            size,
            3,  # thickness
        )


@dataclass(kw_only=True)
class DetectionFamilyData:
    family: Family

    all_corners: Sequence[MatLike]
    all_ids: MatLike
    rejections: Sequence[MatLike]

    detections: list[Detection] = field(default_factory=list)
    annotated_frame: Frame

    @cached_property
    def group(self) -> FamilyGroup:
        return self.family.group

    def add_detection(self, detection: Detection):
        self.detections.append(detection)
        detection.annotate_image_frame_axes(self.annotated_frame.contents)


@dataclass(kw_only=True)
class DetectionData:
    camera: Camera
    original_frame: Frame
    max_id: int

    markers: list[Marker]
    families: list[DetectionFamilyData]

    annotated_frame: Frame = field(init=False)

    def __post_init__(self):
        self.annotated_frame = self.original_frame.copy()

    def family(self, group: FamilyGroup) -> DetectionFamilyData | None:
        for family in self.families:
            if family.group is group:
                return family
        return None

    def add_family_data(
        self,
        family: Family,
        all_corners: Sequence[MatLike],
        all_ids: MatLike,
        rejections: Sequence[MatLike],
    ) -> DetectionFamilyData:
        image = self.original_frame.contents.copy()
        overlay = self.camera.config.overlay

        draw_rejects = overlay.mark_rejections
        detect_color = parse_color(overlay.detection_color)
        reject_color = parse_color(overlay.rejection_color)
        for tgt in (image, self.annotated_frame.contents):
            cv2.aruco.drawDetectedMarkers(
                tgt,
                all_corners,
                all_ids,
                detect_color,
            )
            if draw_rejects:
                cv2.aruco.drawDetectedMarkers(
                    tgt,
                    rejections,
                    None,
                    reject_color,
                )

        family_data = DetectionFamilyData(
            family=family,
            all_corners=all_corners,
            all_ids=all_ids,
            rejections=rejections,
            annotated_frame=self.original_frame.copy(contents=image),
        )
        self.families.append(family_data)

        return family_data

    @property
    def all_detections(self):
        for family in self.families:
            yield from family.detections

    @property
    def all_detected_markers(self):
        for detection in self.all_detections:
            if detection.marker:
                yield detection.marker

    @property
    def all_detected_marker_ids(self):
        for marker in self.all_detected_markers:
            yield marker.id

    @property
    def properties(self):
        return {
            "detections": len(list(self.all_detections)),
            "markers": " ".join(self.all_detected_marker_ids),
        }
