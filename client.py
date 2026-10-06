import socket
import struct
import json
import sys

HOST = '127.0.0.1'
PORT = 9999

OP_CREATE_USER = 1
OP_CREATE_MESSAGE = 2
OP_CREATE_COMPLETION = 3
OP_GET_USERS = 4
OP_GET_MESSAGES = 5
OP_GET_COMPLETIONS = 6
OP_SELECT = 7


class RPCClient:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)  # Таймаут на случай зависания сети
        self.sock.connect((self.host, self.port))

    def _send_request(self, opcode: int, payload: dict):
        body_bytes = json.dumps(payload).encode('utf-8')
        # Запрос: 1 байт opcode + 4 байта len (little-endian)
        header = struct.pack("<BI", opcode, len(body_bytes))
        self.sock.sendall(header + body_bytes)

        # Ответ: 1 байт version + 2 байта opcode + 4 байта len (little-endian)
        resp_header = self.sock.recv(7)
        if not resp_header or len(resp_header) < 7:
            raise ConnectionError("Некорректный заголовок ответа сервера")

        version, resp_opcode, body_len = struct.unpack("<BHI", resp_header)

        resp_body = b""
        while len(resp_body) < body_len:
            chunk = self.sock.recv(body_len - len(resp_body))
            if not chunk:
                break
            resp_body += chunk

        res = json.loads(resp_body.decode('utf-8'))
        if res.get("status") == "ok":
            return res.get("data")
        else:
            raise RuntimeError(res.get("message", "Unknown server error"))

    def create_user(self, ip: str) -> int:
        return self._send_request(OP_CREATE_USER, {"ip": ip})

    def create_message(self, description: str, user_id: int) -> int:
        return self._send_request(OP_CREATE_MESSAGE, {"description": description, "user_id": user_id})

    def create_completion(self, state: str, message_id: int) -> int:
        return self._send_request(OP_CREATE_COMPLETION, {"state": state, "message_id": message_id})

    def get_users(self):
        return self._send_request(OP_GET_USERS, {})

    def get_messages(self):
        return self._send_request(OP_GET_MESSAGES, {})

    def get_completions(self):
        return self._send_request(OP_GET_COMPLETIONS, {})

    def select(self):
        return self._send_request(OP_SELECT, {})

    def close(self):
        self.sock.close()


def repl():
    # Выводим приветствие СРАЗУ с принудительным сбросом буфера
    print("=== RPC REPL запущен ===", flush=True)
    print("Подключение к серверу...", flush=True)

    try:
        client = RPCClient()
        print(" Успешно подключено к серверу 127.0.0.1:9999!", flush=True)
        print("Доступные команды: create_user, create_message, create_completion, get_users, get_messages, get_completions, select, exit\n", flush=True)
    except Exception as e:
        print(f"\n Ошибка подключения: {e}", flush=True)
        print("Убедитесь, что в первом терминале запущен 'py server.py'!", flush=True)
        return

    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue

            if cmd == "create_user":
                ip = input("  IP адрес пользователя: ").strip()
                res = client.create_user(ip)
                print(f"  Создан User ID: {res}\n", flush=True)

            elif cmd == "create_message":
                desc = input("  Текст сообщения: ").strip()
                u_id = int(input("  User ID: ").strip())
                res = client.create_message(desc, u_id)
                print(f"  Создано Message ID: {res}\n", flush=True)

            elif cmd == "create_completion":
                state = input("  Статус (например, SUCCESS): ").strip()
                m_id = int(input("  Message ID: ").strip())
                res = client.create_completion(state, m_id)
                print(f"  Создано Completion ID: {res}\n", flush=True)

            elif cmd == "get_users":
                print(f"  Пользователи: {client.get_users()}\n", flush=True)

            elif cmd == "get_messages":
                print(f"  Сообщения: {client.get_messages()}\n", flush=True)

            elif cmd == "get_completions":
                print(f"  Завершения: {client.get_completions()}\n", flush=True)

            elif cmd == "select":
                print("  Результат выборки (Full Outer Join):", flush=True)
                rows = client.select()
                for row in rows:
                    print(f"    {row}", flush=True)
                print("", flush=True)

            elif cmd in ("exit", "quit"):
                client.close()
                print("Соединение закрыто.", flush=True)
                break
            else:
                print("  Неизвестная команда. Попробуйте еще раз.\n", flush=True)

        except ValueError:
            print("  Ошибка: ID должен быть целым числом!\n", flush=True)
        except KeyboardInterrupt:
            print("\nЗавершение работы...", flush=True)
            client.close()
            break
        except Exception as e:
            print(f"  Ошибка выполнения: {e}\n", flush=True)


if __name__ == "__main__":
    repl()