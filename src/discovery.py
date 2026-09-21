import socket
import threading
import time
from typing import Dict, Tuple

DISCOVERY_PORT = 55554
MAGIC_PREFIX = "NAVAL_HOST"


class RoomBroadcaster:
    def __init__(self, room_name: str, tcp_port: int = 55555):
        self.room_name = room_name
        self.tcp_port = tcp_port
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._thread.start()

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Low timeout so it shuts down promptly
        sock.settimeout(0.5)

        message = f"{MAGIC_PREFIX}:{self.room_name}:{self.tcp_port}".encode("utf-8")
        broadcast_addr = ("<broadcast>", DISCOVERY_PORT)

        while self._running:
            try:
                sock.sendto(message, broadcast_addr)
            except Exception:
                pass
            time.sleep(1.0)

        sock.close()

    def stop(self):
        self._running = False


class RoomListener:
    def __init__(self):
        self.rooms: Dict[str, Tuple[str, int, float]] = {}  # ip -> (room_name, port, last_seen_timestamp)
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", DISCOVERY_PORT))
        except Exception:
            return

        sock.settimeout(0.5)

        while self._running:
            try:
                data, addr = sock.recvfrom(1024)
                text = data.decode("utf-8")
                if text.startswith(MAGIC_PREFIX):
                    parts = text.split(":")
                    if len(parts) == 3:
                        _, room_name, port_str = parts
                        host_ip = addr[0]
                        self.rooms[host_ip] = (room_name, int(port_str), time.time())
            except socket.timeout:
                pass
            except Exception:
                break

            now = time.time()
            self.rooms = {ip: info for ip, info in self.rooms.items() if now - info[2] < 4.0}

        sock.close()

    def get_available_rooms(self) -> Dict[str, Tuple[str, int]]:
        now = time.time()
        return {ip: (info[0], info[1]) for ip, info in self.rooms.items() if now - info[2] < 4.0}

    def stop(self):
        self._running = False
