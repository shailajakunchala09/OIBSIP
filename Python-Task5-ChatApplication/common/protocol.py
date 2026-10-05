"""Wire protocol shared by server and client.

Every message is one JSON object encoded as UTF-8 and terminated by a newline.
"""
from __future__ import annotations

import json
import socket
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050
MAX_FRAME_BYTES = 64 * 1024


class ProtocolError(Exception):
    """Raised when the peer sends something that is not a valid frame."""


def encode(message: dict[str, Any]) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"


class FrameReader:
    """Reads newline-delimited JSON frames from a socket."""

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buffer = b""

    def read(self) -> dict[str, Any] | None:
        """Return the next frame, or None when the peer closed the connection.

        socket.timeout / OSError propagate to the caller.
        """
        while b"\n" not in self._buffer:
            if len(self._buffer) > MAX_FRAME_BYTES:
                raise ProtocolError("Frame too large")
            chunk = self._sock.recv(4096)
            if not chunk:
                return None
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        try:
            frame = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("Malformed frame") from exc
        if not isinstance(frame, dict) or "type" not in frame:
            raise ProtocolError("Frame must be an object with a 'type'")
        return frame
