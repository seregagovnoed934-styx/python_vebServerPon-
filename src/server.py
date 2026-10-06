import socket
import struct
import json
import time
import main as db  # используем функции из первого этапа

HOST = '127.0.0.1'
PORT = 9999

# Коды операций (Opcodes)
OP_CREATE_USER = 1
OP_CREATE_MESSAGE = 2
OP_CREATE_COMPLETION = 3
OP_GET_USERS = 4
OP_GET_MESSAGES = 5
OP_GET_COMPLETIONS = 6
OP_SELECT = 7

PROTOCOL_VERSION = 1


def handle_request(opcode: int, payload: dict):
    if opcode == OP_CREATE_USER:
        res = db.create_user(payload["ip"])
        return {"status": "ok", "data": res}
    elif opcode == OP_CREATE_MESSAGE:
        res = db.create_message(payload["description"], payload["user_id"])
        return {"status": "ok", "data": res}
    elif opcode == OP_CREATE_COMPLETION:
        res = db.create_completion(payload["state"], payload["message_id"])
        return {"status": "ok", "data": res}
    elif opcode == OP_GET_USERS:
        return {"status": "ok", "data": db.get_users()}
    elif opcode == OP_GET_MESSAGES:
        return {"status": "ok", "data": db.get_messages()}
    elif opcode == OP_GET_COMPLETIONS:
        return {"status": "ok", "data": db.get_completions()}
    elif opcode == OP_SELECT:
        return {"status": "ok", "data": db.select()}
    else:
        return {"status": "error", "message": "Unknown opcode"}


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Запущен на {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        try:
            while True:
                # Чтение заголовка запроса: 1 байт opcode + 4 байта payload_len (little-endian)
                header = conn.recv(5)
                if not header or len(header) < 5:
                    break
                
                opcode, body_len = struct.unpack("<BI", header)
                
                # Чтение тела
                body_bytes = b""
                while len(body_bytes) < body_len:
                    chunk = conn.recv(body_len - len(body_bytes))
                    if not chunk:
                        break
                    body_bytes += chunk
                
                payload = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
                
                # Выполнение бизнес-логики
                response_data = handle_request(opcode, payload)
                response_body = json.dumps(response_data).encode('utf-8')
                
                # Формирование ответа: 1 байт version + 2 байта opcode + 4 байта length (little-endian)
                resp_header = struct.pack("<BHI", PROTOCOL_VERSION, opcode, len(response_body))
                conn.sendall(resp_header + response_body)
                
                # Встроенное журналирование ответа в stdout (требование ТЗ)
                print(f"[LOG {time.strftime('%H:%M:%S')}] Response -> Opcode: {opcode}, Status: {response_data.get('status')}, BodyLen: {len(response_body)}")

        except Exception as e:
            print(f"[SERVER ERROR] {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    start_server()