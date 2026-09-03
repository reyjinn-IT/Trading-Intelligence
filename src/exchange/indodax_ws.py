import asyncio
import json
import logging
import threading
import time
from typing import Dict, Any, Callable, List, Optional
import websockets
from src.core.config import settings

logger = logging.getLogger("IndodaxWebSocket")

class IndodaxWSClient:
    def __init__(self, ws_url: Optional[str] = None):
        self.ws_url = ws_url or settings.INDODAX_WS_URL
        self.running = False
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.latest_data: Dict[str, Any] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def add_listener(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        self.callbacks.append(cb)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_thread, daemon=True, name="IndodaxWS")
        self._thread.start()
        logger.info("Indodax WebSocket client started.")

    def stop(self) -> None:
        self.running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("Indodax WebSocket client stopped.")

    def _run_thread(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen())

    async def _connect_and_listen(self) -> None:
        while self.running:
            try:
                # Attempt connection to Indodax WS endpoint
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info("Connected to Indodax WebSocket.")
                    while self.running:
                        msg = await ws.recv()
                        try:
                            data = json.loads(msg)
                            self.latest_data = data
                            for cb in self.callbacks:
                                try:
                                    cb(data)
                                except Exception as e:
                                    logger.error("Error in WS callback: %s", e)
                        except Exception as parse_err:
                            logger.debug("WS non-json message: %s", parse_err)
            except Exception as e:
                logger.debug("WebSocket connection dropped or unavailable (%s). Retrying in 5s...", e)
                # Fallback heartbeat so system remains responsive
                await asyncio.sleep(5)

indodax_ws = IndodaxWSClient()
