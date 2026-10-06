"""Модуль клиентуры для RPC взаимодействия по TCP."""

import json
import socket
import struct

HOST = "127.0.0.1"
PORT = 9999

OP_CREATE_USER = 1
OP_CREATE_MESSAGE = 2
OP_CREATE_COMPLETION = 3
OP_GET_USERS = 4
OP_GET_MESSAGES = 5
OP_GET_COMPLETIONS = 6
OP_SELECT = 7


class RPCClient:
    """Класс клиентского сетевого подключения."""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.host, self.port))

    def _send_request(self, opcode: int, payload: dict):
        body_bytes = json.dumps(payload).encode("utf-8")
        header = struct.pack("<BI", opcode, len(body_bytes))
        self.sock.sendall(header + body_bytes)

        resp_hdr = self.sock.recv(7)
        if not resp_hdr or len(resp_hdr) < 7:
            raise ConnectionError("Invalid response header")

        _, _, body_len = struct.unpack("<BHI", resp_hdr)
        resp_body = b""
        while len(resp_body) < body_len:
            chunk = self.sock.recv(body_len - len(resp_body))
            if not chunk:
                break
            resp_body += chunk

        res = json.loads(resp_body.decode("utf-8"))
        if res.get("status") == "ok":
            return res.get("data")
        raise RuntimeError(res.get("message", "Error"))

    def create_user(self, ip: str) -> int:
        """Создать пользователя через RPC."""
        return self._send_request(OP_CREATE_USER, {"ip": ip})

    def create_message(self, description: str, user_id: int) -> int:
        """Создать сообщение через RPC."""
        payload = {"description": description, "user_id": user_id}
        return self._send_request(OP_CREATE_MESSAGE, payload)

    def create_completion(self, state: str, message_id: int) -> int:
        """Создать статус выполнения через RPC."""
        payload = {"state": state, "message_id": message_id}
        return self._send_request(OP_CREATE_COMPLETION, payload)

    def get_users(self):
        """Запросить список пользователей."""
        return self._send_request(OP_GET_USERS, {})

    def get_messages(self):
        """Запросить список сообщений."""
        return self._send_request(OP_GET_MESSAGES, {})

    def get_completions(self):
        """Запросить список статусов."""
        return self._send_request(OP_GET_COMPLETIONS, {})

    def select(self):
        """Запросить сложную выборку."""
        return self._send_request(OP_SELECT, {})

    def close(self):
        """Закрыть сетевое соединение."""
        self.sock.close()


def run_demo():
    """Запуск демонстрационного сценария."""
    client = RPCClient()
    u_id = client.create_user("127.0.0.1")
    m_id = client.create_message("Test message", u_id)
    client.create_completion("SUCCESS", m_id)

    print("Пользователи:", client.get_users())
    print("Сообщения:", client.get_messages())
    print("Результат выборки:", client.select())

    client.close()


if __name__ == "__main__":
    run_demo()