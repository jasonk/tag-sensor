from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field, fields
from pathlib import Path

import structlog

from .calibration import Calibrator
from .camera import Camera, CameraConfig, CameraNotFoundError
from .config import Config
from .detection import Detection, DetectionData
from .emitter import emit
from .family import ALL_FAMILY_GROUPS
from .frame import Frame
from .interfaces import BaseInterface, Interface, make_interface
from .marker import Marker, MarkerNotFoundError, MarkerConfig
from .utils import apply_defaults

logger = structlog.get_logger()


@dataclass(kw_only=True)
class Manager:
    config: Config = field(init=False)
    detections: list[Detection] = field(default_factory=list, init=False)

    _markers: dict[str, Marker] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _cameras: dict[str, Camera] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    interfaces: dict[str, Interface] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    update_interval: float = 60.0

    @property
    def markers(self) -> list[Marker]:
        return list(self._markers.values())

    @property
    def cameras(self) -> list[Camera]:
        return list(self._cameras.values())

    def get_marker(self, marker_id: str | int):
        if isinstance(marker_id, str) and marker_id.isnumeric():
            marker_id = int(marker_id)
        if isinstance(marker_id, str):
            marker = self._markers.get(marker_id)
            if marker is not None:
                return marker
        if isinstance(marker_id, int):
            for marker in self.markers:
                if marker.config.tag_id == marker_id:
                    return marker
        return None

    def marker(self, marker_id: str | int) -> Marker:
        marker = self.get_marker(marker_id)
        if not marker:
            raise MarkerNotFoundError(marker_id)
        return marker

    def setup_marker(self, marker_id: str | MarkerConfig, **kwargs):
        if isinstance(marker_id, MarkerConfig):
            marker = Marker(config=marker_id)
        else:
            marker_defaults = self.config.marker_defaults.model_dump()
            apply_defaults(kwargs, marker_defaults)
            config = MarkerConfig(**kwargs)
            marker = Marker(config=config)

        self._markers[marker.id] = marker

    def get_camera(self, camera_id: str):
        return self._cameras.get(camera_id)

    def camera(self, camera_id: str) -> Camera:
        camera = self.get_camera(camera_id)
        if not camera:
            raise CameraNotFoundError(camera_id)
        return camera

    def setup_camera(self, camera_id: str | CameraConfig, **kwargs):
        default_interface = self.config.camera_defaults.interface
        default_data_dir = self.config.camera_data_dir

        if isinstance(camera_id, CameraConfig):
            config = camera_id
        else:
            camera_defaults = self.config.camera_defaults.model_dump()
            apply_defaults(kwargs, camera_defaults)
            config = CameraConfig(**kwargs)

        def get_iface(conf: CameraConfig) -> Interface | None:
            if isinstance(conf.interface, str):
                return self.interfaces.get(conf.interface)
            if conf.interface:
                return make_interface(conf.interface)
            if isinstance(default_interface, str):
                return self.interfaces.get(default_interface)
            if default_interface:
                return make_interface(default_interface)
            return None

        iface = get_iface(config)
        if iface is None:  # pragma: no cover
            logger.error(
                "Skipping camera without interface",
                camera_id=config.id,
            )
            return
        data_dir = config.data_dir or default_data_dir.joinpath(config.id)
        camera = Camera(
            config=config,
            interface=iface,
            directory=data_dir,
        )
        self._cameras[camera.id] = camera

    def load_config(self, config_file: Path | str):
        config = Config.load(config_file)
        self.config = config

        self.interfaces = {
            key: make_interface(value)
            for key, value in self.config.interfaces.items()
        }
        for mconf in self.config.markers:
            self.setup_marker(mconf)
        for cconf in self.config.cameras:
            self.setup_camera(cconf)

    async def get_detections(self):
        for camera in self.cameras:
            if camera.config.ignore_detections:
                continue
            try:
                async for det in self.get_detections_for_camera(camera):
                    yield det
            except Exception:
                logger.exception(
                    "Failed to get detections",
                    camera=camera.id,
                )

    async def get_frame(self, camera: Camera) -> Frame | None:
        iface = camera.interface
        if not iface:
            return None  # pragma: no cover
        try:
            res = await iface.get_frame(camera)
            if res is None:  # pragma: no cover
                camera.is_available = False
                return None
            camera.is_available = True
            return res  # noqa: TRY300
        # pylint: disable-next=bare-except
        except:  # noqa: E722 # pragma: no cover
            logger.exception("Failed to get frame", camera=camera.id)
            camera.is_available = False
            return None

    original_frames: dict[str, Frame] = field(
        init=False,
        repr=False,
        default_factory=dict,
    )

    async def get_detections_for_camera(
        self,
        camera: Camera,
    ) -> AsyncGenerator[Detection, None]:
        data = await self.get_detection_data_for_camera(camera)
        if data is None:
            return  # pragma: no cover

        camera.update(data)
        for detection in data.all_detections:
            yield detection

    async def get_detection_data_for_camera(
        self,
        camera: Camera,
    ) -> DetectionData | None:
        original = await self.get_frame(camera)
        if original is None:
            return None  # pragma: no cover
        grayscale = original.grayscale()

        markers = self.markers_for_camera(camera)
        families = (
            {m.family for m in markers} if markers else set(ALL_FAMILY_GROUPS)
        )
        max_id = max(m.config.tag_id for m in markers)
        data = DetectionData(
            camera=camera,
            original_frame=original,
            markers=list(markers),
            families=[],
            max_id=max_id,
        )
        for family in families:
            detector = family.detector(max_id)

            all_corners, all_ids, rejections = detector.detectMarkers(
                grayscale.contents,
            )
            family_data = data.add_family_data(
                family=family,
                all_corners=all_corners,
                all_ids=all_ids,
                rejections=rejections,
            )

            if all_ids is None:
                continue

            for _id, corners in zip(
                all_ids.flatten(),
                all_corners,
                strict=True,
            ):
                detection = Detection(
                    camera=camera,
                    family=family,
                    original_frame=original,
                    tag_id=int(_id),
                    corners=corners,
                    marker=self.get_marker(int(_id)),
                )
                family_data.add_detection(detection)
        return data

    async def update_detections(self) -> None:
        logger.debug("Updating detections")
        detections: list[Detection] = [d async for d in self.get_detections()]
        self.detections = detections
        emit("detections", detections=detections)

        for marker in self.markers:
            self.update_marker(
                marker,
                [d for d in detections if d.tag_id == marker.config.tag_id],
            )

    def update_marker(
        self,
        marker: Marker,
        detections: list[Detection],
    ):
        detection: Detection | None = None
        if len(detections) > 1:
            detection = max(detections, key=lambda d: d.sort_distance)
        elif len(detections) == 1:
            detection = detections[0]
        else:
            detection = None

        original_frame: Frame | None = None
        annotated_frame: Frame | None = None
        if detection and detection.original_frame:
            original_frame = detection.original_frame
            annotated_frame = detection.annotated_frame
        elif len(marker.cameras) == 1:
            camera = self.camera(marker.cameras[0])
            original_frame = camera.original_frame

        marker.update(
            detection=detection,
            detections=detections,
            original_frame=original_frame,
            annotated_frame=annotated_frame,
        )

    def get_calibrator(self, camera: Camera | str):
        if isinstance(camera, str):
            camera = self.camera(camera)
        if not camera.calibrator:
            camera.calibrator = Calibrator(manager=self, camera=camera)
        return camera.calibrator

    def markers_for_camera(self, camera: Camera):
        markers: set[Marker] = set()
        for marker in self.markers:
            if marker.cameras and camera.id not in marker.cameras:
                continue
            markers.add(marker)
        return markers

    def all_interfaces(self):
        return list(self.interfaces.values()) + [
            camera.interface
            for camera in self.cameras
            if isinstance(camera.interface, BaseInterface)
        ]

    async def prepare(self):
        for iface in self.all_interfaces():
            await iface.start()

    async def start(self):
        await self.prepare()

    async def stop(self):
        for iface in self.all_interfaces():
            await iface.stop()

    def __rich_repr__(self):  # pragma: no cover
        for f in fields(self):
            if f.name.startswith("_"):
                continue
            yield f.name, getattr(self, f.name), None
