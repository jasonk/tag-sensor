from __future__ import annotations

# from collections.abc import Callable
from typing import TYPE_CHECKING

# from prometheus_fastapi_instrumentator.metrics import Info
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

if TYPE_CHECKING:
    from fastapi import FastAPI

    from tag_sensor.manager import Manager

markers_gauge = Gauge("markers_total", "Number of markers.")
cameras_gauge = Gauge("cameras_total", "Number of cameras.")
active_detections_gauge = Gauge(
    "active_detections_total",
    "Number of active detections.",
)

instrumentator = Instrumentator(
    #   should_group_status_codes = False,
    #   should_ignore_untemplated = True,
    #   should_respect_env_var = True,
    #   should_instrument_requests_inprogress = True,
    #   excluded_handlers = [
    #       # '.*admin.*',
    #       '/metrics',
    #   ],
    #   env_var_name = 'ENABLE_METRICS',
    #   inprogress_name = 'inprogress',
    #   inprogress_labels = True,
)


def setup_metrics(app: FastAPI, manager: Manager) -> None:
    markers_gauge.set_function(lambda: len(manager.markers))
    cameras_gauge.set_function(lambda: len(manager.cameras))
    active_detections_gauge.set_function(lambda: len(manager.detections))

    instrumentator.expose(app)
