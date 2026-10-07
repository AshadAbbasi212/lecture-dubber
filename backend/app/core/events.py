import asyncio
import json
from typing import Dict, Set, Any
from backend.app.core.logging import logger


class EventBroadcaster:
    """Pub/sub broker for job progress Server-Sent Events (SSE)."""
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._lock:
            if job_id not in self._subscribers:
                self._subscribers[job_id] = set()
            self._subscribers[job_id].add(queue)
        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].discard(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]

    async def broadcast(self, job_id: str, event_data: dict) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(job_id, []))
        
        for q in queues:
            try:
                await q.put(event_data)
            except Exception as e:
                logger.debug(f"Failed to put event into queue for job {job_id}: {e}")

    def broadcast_sync(self, job_id: str, event_data: dict) -> None:
        """Helper to broadcast from synchronous threads/workers."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(job_id, event_data), loop)
        except RuntimeError:
            pass


broadcaster = EventBroadcaster()
