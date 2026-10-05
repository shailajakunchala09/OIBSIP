"""Network layer for the desktop client.

All socket work happens on background threads. Results are delivered through
`ChatClient.events`, a thread-safe queue that the GUI drains with Tk's after().
Frames from the server are put on the queue unchanged; three synthetic frames
describe the connection itself: `_connected`, `_connect_failed` and `_disconnected`.
"""
from __future__ import annotations

import queue
import socket
import threading
from typing import Any

from common.protocol import FrameReader, ProtocolError, encode

CONNECT_TIMEOUT = 4.0
IDLE_TIMEOUT = 45.0     # matches the server; heartbeat keeps healthy links alive
PING_INTERVAL = 15.0


def friendly_connect_error(exc: OSError, host: str, port: int) -> str:
    if isinstance(exc, ConnectionRefusedError):
        return (f"Could not reach the server at {host}:{port}. "
                "Start it first (run_server.bat), then try again.")
    if isinstance(exc, socket.timeout):
        return f"The server at {host}:{port} did not respond in time."
    if isinstance(exc, socket.gaierror):
        return f"'{host}' is not a valid server address."
    return f"Could not connect to {host}:{port} ({exc.strerror or exc})."


class ChatClient:
    def __init__(self) -> None:
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._sock: socket.socket | None = None
        self._generation = 0

    # -- connection ------------------------------------------------------
    def connect_async(self, host: str, port: int) -> None:
        threading.Thread(target=self._connect, args=(host, port), name="connect", daemon=True).start()

    def _connect(self, host: str, port: int) -> None:
        self.close()
        try:
            sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
        except OSError as exc:
            self.events.put({"type": "_connect_failed", "message": friendly_connect_error(exc, host, port)})
            return
        sock.settimeout(IDLE_TIMEOUT)
        stop = threading.Event()
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._sock = sock
        self.events.put({"type": "_connected"})
        threading.Thread(target=self._read_loop, args=(sock, generation, stop), name="reader", daemon=True).start()
        threading.Thread(target=self._heartbeat, args=(generation, stop), name="heartbeat", daemon=True).start()

    def close(self) -> None:
        """Close the current connection quietly (no `_disconnected` event)."""
        with self._lock:
            self._generation += 1
            sock, self._sock = self._sock, None
        self._shutdown(sock)

    @property
    def connected(self) -> bool:
        return self._sock is not None

    @staticmethod
    def _shutdown(sock: socket.socket | None) -> None:
        if sock is None:
            return
        for action in (lambda: sock.shutdown(socket.SHUT_RDWR), sock.close):
            try:
                action()
            except OSError:
                pass

    def _lost(self, generation: int, reason: str) -> None:
        with self._lock:
            if generation != self._generation:
                return          # we closed it ourselves, or a newer connection replaced it
            self._generation += 1
            sock, self._sock = self._sock, None
        self._shutdown(sock)
        self.events.put({"type": "_disconnected", "reason": reason})

    # -- threads ---------------------------------------------------------
    def _read_loop(self, sock: socket.socket, generation: int, stop: threading.Event) -> None:
        reader = FrameReader(sock)
        reason = "The connection to the server was closed."
        try:
            while True:
                frame = reader.read()
                if frame is None:
                    break
                self.events.put(frame)
        except socket.timeout:
            reason = "The server stopped responding."
        except ProtocolError:
            reason = "The server sent data this client could not understand."
        except OSError:
            pass
        finally:
            stop.set()
            self._lost(generation, reason)

    def _heartbeat(self, generation: int, stop: threading.Event) -> None:
        while not stop.wait(PING_INTERVAL):
            if generation != self._generation:
                return
            self.send("ping")

    # -- sending ---------------------------------------------------------
    def send(self, kind: str, **payload: Any) -> bool:
        with self._lock:
            sock, generation = self._sock, self._generation
        if sock is None:
            return False
        try:
            with self._send_lock:
                sock.sendall(encode({"type": kind, **payload}))
            return True
        except OSError:
            self._lost(generation, "The connection to the server was lost.")
            return False
