from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import AsyncIterator

from backend.api.schemas import EventPayload


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, project_id: str, *, kind: str, message: str) -> None:
        payload = EventPayload(projectId=project_id, kind=kind, message=message, timestamp=datetime.now(timezone.utc))
        serialized = f"data: {payload.model_dump_json(by_alias=True)}\n\n"
        async with self._lock:
            for queue in list(self._subscribers[project_id]):
                await queue.put(serialized)

    async def stream(self, project_id: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers[project_id].append(queue)
        try:
            yield f"event: ping\ndata: {json.dumps({'projectId': project_id})}\n\n"
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                subscribers = self._subscribers.get(project_id, [])
                if queue in subscribers:
                    subscribers.remove(queue)


_broker = EventBroker()


def get_event_broker() -> EventBroker:
    return _broker
