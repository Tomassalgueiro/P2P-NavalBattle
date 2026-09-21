import json
import queue
import socket
import threading 
from typing import Optional, Tuple

DEFAULT_PORT = 55555
BUFFER_SIZE = 4096

class NetworkManager: 
    def __init__(self) -> None:
        self.sock: Optional[socket.socket] = None
        self.server_sock: Optional[socket.socket] = None
        self.inbox: queue.Queue = queue.Queue()
        self.isConnected = False
        self.isHost = False
        self._running = False
        self._send_lock = threading.Lock()

    def start_host(self, port: int = DEFAULT_PORT) -> bool:
        self.isHost = True
        self._running = True

        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(("0.0.0.0", port))
            self.server_sock.listen(1)

            threading.Thread(target=self._host_accept_loop, daemon=True).start()
            return True

        except Exception as e:

            print(f"[Network] Failed to start host: {e}")
            self.close()
            return False

    def connect_to_host(self, host_ip: str, port: int = DEFAULT_PORT) -> None:

        self.isHost = False
        self._running = True

        threading.Thread(
            target=self._client_connect_loop,
            args=(host_ip, port),
            daemon=True
        ).start()

    def _host_accept_loop(self) -> None:

        try:
            client_conn, addr = self.server_sock.accept()
            self.sock = client_conn
            self.isConnected = True
            print(f"[Network] Peer connected from {addr[0]}:{addr[1]}")
            self._receive_loop()
        except Exception as e:
            if self._running:
                print(f"[Network] Host accept error: {e}")
                self.close()

    def _client_connect_loop(self, host_ip: str, port: int) -> None:

        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect((host_ip, port))
            self.sock = client_sock
            self.isConnected = True
            print(f"[Network] Connected to host at {host_ip}:{port}")
            self._receive_loop()
        except Exception as e:
            print(f"[Network] Failed to connect to host: {e}")
            self.close()

    def _receive_loop(self) -> None:
        buffer = ""

        while self._running and self.sock:
            try:
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    print("[Network] Peer disconnected.")
                    break

                buffer += data.decode("utf-8")

                # Process all complete newline-delimited payloads
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            self.inbox.put(msg)
                        except json.JSONDecodeError as decode_err:
                            print(f"[Network] Malformed JSON received: {decode_err}")

            except (ConnectionResetError, ConnectionAbortedError):
                print("[Network] Connection was reset by peer.")
                break
            except Exception as e:
                if self._running:
                    print(f"[Network] Receive error: {e}")
                break

        self.close()

    def send_message(self, data: dict) -> bool:

        if not self.isConnected or not self.sock:
            return False

        try:

            payload = (json.dumps(data) + "\n").encode("utf-8")
            with self._send_lock:
                self.sock.sendall(payload)
            return True
        except Exception as e:
            print(f"[Network] Send failed: {e}")
            self.close()
            return False

    def get_message(self) -> Optional[dict]:

        try:
            return self.inbox.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        self._running = False
        self.isConnected = False

        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None

