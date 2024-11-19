from __future__ import annotations

import os

from pydantic import SecretStr

from tag_sensor.model import Model


class MQTTBrokerConfig(Model):
    host: str = os.getenv("MQTT_HOST", "localhost")
    port: int = int(os.getenv("MQTT_PORT", "1883"))
    username: str = os.getenv("MQTT_USERNAME", "")
    password: SecretStr = SecretStr(os.getenv("MQTT_PASSWORD", ""))
