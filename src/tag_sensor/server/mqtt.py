from __future__ import annotations

import asyncio
from asyncio import Queue, Task
from collections.abc import Generator
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from aiomqtt import Client, Will, Message
from prometheus_client import Counter
import structlog

from tag_sensor.emitter import add_event_listener
from tag_sensor.manager import Manager
from tag_sensor.marker import Marker
from tag_sensor.server.utils import shutting_down

logger = structlog.get_logger()

messages_sent_counter = Counter(
    "mqtt_messages_sent_total",
    "Number of MQTT messages sent.",
    labelnames=("topic",),
)
commands_received_counter = Counter(
    "mqtt_commands_received_total",
    "Number of MQTT commands received.",
)


@dataclass
class Action:
    action: str
    data: Any = None
    target: str | None = None


class MQTTHelper:
    client: Client
    manager: Manager
    queue: Queue[Action]

    will_topic = "tag-sensor/availability"

    def __init__(self, manager: Manager):
        config = manager.config

        host = config.broker.host
        port = config.broker.port
        username = config.broker.username

        self.client = Client(
            host,
            port,
            username=username,
            password=config.broker.password.get_secret_value(),
            will=Will(topic=self.will_topic, payload="offline", retain=True),
            keepalive=2,
        )
        self.manager = manager
        self.queue = Queue[Action]()
        add_event_listener("marker:updated", self.on_marker_updated)

    def on_marker_updated(self, marker: Marker):
        self.action("update_marker", marker, marker.id)

    tasks: list[Task]

    async def set_available(self, online: bool):
        logger.debug("Setting availability", online=online)
        await self.client.publish(
            self.will_topic,
            "online" if online else "offline",
        )

    async def __aenter__(self):
        await self.client.__aenter__()

        await self.set_available(True)
        loop = asyncio.get_event_loop()
        self.enqueue_init_tasks()
        self.tasks = [
            loop.create_task(task)
            for task in (
                self.handle_commands(),
                self.enqueue_updates(),
                self.listen_for_commands(),
            )
        ]
        return self

    async def __aexit__(self, *args):  # type: ignore # noqa: ANN002
        await self.set_available(False)
        await self.client.__aexit__(*args)

        async def finish(task: Task[Any]):
            with suppress(asyncio.CancelledError):
                task.cancel()
                await task

        await asyncio.gather(*(finish(t) for t in self.tasks))

    def _process_command_message(self, message: Message):
        commands_received_counter.labels().inc()
        topic = message.topic
        if topic == "homeassistant/status":
            msg = message.payload
            logger.debug("Home Assistant status", status=msg)
            if msg == "online":
                self.enqueue_init_tasks()
            return
        if not topic.matches("tag-sensor/#"):
            return
        if topic == "tag-sensor/command":
            logger.debug(
                "MQTT Command",
                command=message.payload,
                topic=message.topic,
            )
            return
        if topic.matches("tag-sensor/+/command"):
            logger.debug(
                "MQTT Item Command",
                command=message.payload,
                topic=message.topic,
            )
            target = str(topic).split("/")[1]
            return

        if topic.matches("tag-sensor/+/config"):
            target = str(topic).split("/")[1]
            self.action("configure", message.payload, target)
            return

    async def listen_for_commands(self):
        await self.client.subscribe("tag-sensor/+/config")
        await self.client.subscribe("tag-sensor/+/command")
        await self.client.subscribe("tag-sensor/command")
        await self.client.subscribe("homeassistant/status")
        async for message in self.client.messages:
            self._process_command_message(message)

    async def handle_commands(self):
        while not shutting_down.is_set():
            act = await self.queue.get()
            logger.debug(
                "Handling action", action=act.action, target=act.target
            )

            match act.action:
                case "update_configurations":
                    await self.update_configurations()
                case "update_detections":
                    await self.manager.update_detections()
                case "update_marker":
                    await self.publish_from(act.data.publish())
                case other:
                    logger.error("Unknown action", action=other)
            self.queue.task_done()

    async def publish(self, topic: str, data: str):
        logger.debug("PUBLISHING", topic=topic)

        await self.client.publish(topic, data)
        messages_sent_counter.labels(topic).inc()

    async def publish_from(
        self,
        source: Generator[tuple[str, str], None, None],
    ):
        for topic, data in source:
            await self.publish(topic, data)

    def action(
        self,
        action: str,
        data: Any = None,
        target: str | None = None,
    ):
        return self.queue.put_nowait(Action(action, data, target))

    async def update_configurations(self):
        for item in self.manager.markers + self.manager.cameras:
            await self.publish_from(item.configure())

    async def enqueue_updates(self):
        while not shutting_down.is_set():
            await asyncio.sleep(self.manager.config.update_interval)
            self.action("update_detections")

    def enqueue_init_tasks(self):
        self.action("update_configurations")
        self.action("update_detections")
