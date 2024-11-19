from __future__ import annotations

from .calibration import Calibrator
from .camera import Camera, CameraConfig, CameraConfigDefaults
from .config import Config
from .detection import Detection
from .family import (
    Family,
    FamilyGroup,
    FamilySize,
    get_family,
    get_family_size,
)
from .frame import Frame
from .manager import Manager
from .marker import (
    Attr,
    Attrs,
    Marker,
    MarkerConfig,
    MarkerConfigDefaults,
)
from .model import Model
from .renderer import (
    Block,
    MarkerPNG,
    MarkerPNGConfig,
    MarkerRenderer,
    MarkerRendererConfig,
    MarkerSTL,
    MarkerSTLConfig,
    MarkerSVG,
    MarkerSVGConfig,
    render_text,
)
from .utils import (
    add_text_to_image,
    parse_color,
    fill_template,
    fill_templates,
    NotFoundError,
    apply_defaults,
)

__all__ = (
    "Attr",
    "Attrs",
    "Block",
    "Calibrator",
    "Camera",
    "CameraConfig",
    "CameraConfigDefaults",
    "Config",
    "Detection",
    "Family",
    "FamilyGroup",
    "FamilySize",
    "Frame",
    "Manager",
    "Marker",
    "MarkerConfig",
    "MarkerConfigDefaults",
    "MarkerPNG",
    "MarkerPNGConfig",
    "MarkerRenderer",
    "MarkerRendererConfig",
    "MarkerSTL",
    "MarkerSTLConfig",
    "MarkerSVG",
    "MarkerSVGConfig",
    "Model",
    "NotFoundError",
    "add_text_to_image",
    "apply_defaults",
    "fill_template",
    "fill_templates",
    "get_family",
    "get_family_size",
    "parse_color",
    "render_text",
)
