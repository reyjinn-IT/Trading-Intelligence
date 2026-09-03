import time
import threading
import logging
from typing import Optional, Callable, List

logger = logging.getLogger("DeadmanSwitch")

class DeadmanSwitch:
    def __init__(self, timeout_seconds: int = 30, on_timeout_callback: Optional[Callable[[], None]] = None):
        self.timeout_seconds = timeout_seconds
        self.on_timeout_callback = on_timeout_callback
        self.last_heartbeat = time.time()
        self.is_armed = False
        self.is_triggered = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.cancel_callbacks: List[Callable[[], None]] = []

    def register_cancel_callback(self, cb: Callable[[], None]) -> None:
        self.cancel_callbacks.append(cb)

    def arm(self) -> None:
        with self._lock:
            self.last_heartbeat = time.time()
            self.is_armed = True
            self.is_triggered = False
            self._stop_event.clear()

        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="DeadmanMonitor")
            self._thread.start()
            logger.info("Deadman Switch ARMED. Timeout: %d seconds.", self.timeout_seconds)

    def disarm(self) -> None:
        with self._lock:
            self.is_armed = False
            self._stop_event.set()
        logger.info("Deadman Switch DISARMED.")

    def heartbeat(self) -> None:
        with self._lock:
            self.last_heartbeat = time.time()
            if self.is_triggered:
                logger.warning("Heartbeat received while Deadman was triggered. Call reset() to re-enable trading.")

    def reset(self) -> None:
        with self._lock:
            self.last_heartbeat = time.time()
            self.is_triggered = False
            self.is_armed = True
        logger.info("Deadman Switch manually RESET and re-armed.")

    def get_status(self) -> dict:
        elapsed = time.time() - self.last_heartbeat
        remaining = max(0.0, self.timeout_seconds - elapsed)
        return {
            "armed": self.is_armed,
            "triggered": self.is_triggered,
            "timeout_seconds": self.timeout_seconds,
            "elapsed_seconds": round(elapsed, 2),
            "remaining_seconds": round(remaining, 2),
            "is_safe": not self.is_triggered and (not self.is_armed or elapsed < self.timeout_seconds)
        }

    def _trigger_emergency(self) -> None:
        with self._lock:
            if self.is_triggered:
                return
            self.is_triggered = True

        logger.critical("DEADMAN SWITCH TRIGGERED! Heartbeat timed out (%ds). Cancelling all open orders...", self.timeout_seconds)
        
        # Execute order cancellation callbacks
        for cb in self.cancel_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error("Error executing emergency callback: %s", e)

        if self.on_timeout_callback:
            try:
                self.on_timeout_callback()
            except Exception as e:
                logger.error("Error executing on_timeout_callback: %s", e)

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(1.0)
            with self._lock:
                if not self.is_armed:
                    continue
                elapsed = time.time() - self.last_heartbeat

            if elapsed >= self.timeout_seconds and not self.is_triggered:
                self._trigger_emergency()

# Global deadman instance
deadman_switch = DeadmanSwitch(timeout_seconds=30)
