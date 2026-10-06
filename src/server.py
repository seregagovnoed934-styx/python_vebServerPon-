"""Модуль TCP RPC сервера с поддержкой бинарного протокола."""

import json
import socket
import struct
import sys

from src import main as db

HOST = "127.0.0.1"
PORT = 9999
PROTOCOL_VERSION = 1
MAX_CONNECTIONS = 5
REQ_HEADER_SIZE = 5

OP_CREATE_USER = 1
OP_CREATE_MESSAGE = 2
OP_CREATE_COMPLETION = 3
OP_GET_USERS = 4
OP_GET_MESSAGES = 5
OP_GET_COMPLETIONS = 6
OP_SELECT = 7


def handle_request(opcode: int, payload: dict) -> dict:
    """Обрабатывает запросы и вызывает соответствующие методы БД."""
    if opcode == OP_CREATE_USER:
        return {"status": "ok", "data": db.create_user(payload["ip"])}
    if opcode == OP_CREATE_MESSAGE:
        res = db.create_message(
            payload["description"], payload["user_id"]
        )
        return {"status": "ok", "data": res}
    if opcode == OP_CREATE_COMPLETION:
        res = db.create_completion(
            payload["state"], payload["message_id"]
        )
        return {"status": "ok", "data": res}
    if opcode == OP_GET_USERS:
        return {"status": "ok", "data": db.get_users()}
    if opcode == OP_GET_MESSAGES:
        return {"status": "ok", "data": db.get_messages()}
    if opcode == OP_GET_COMPLETIONS:
        return {"status": "ok", "data": db.get_completions()}
    if opcode == OP_SELECT:
        return {"status": "ok", "data": db.select()}
    return {"status": "error", "message": "Unknown opcode"}


def read_exact(conn: socket.socket, length: int) -> bytes:
    """Считывает точное количество байт из сокета."""
    data = b""
    while len(data) < length:
        chunk = conn.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return data


def _process_client_connection(conn: socket.socket):
    """Обрабатывает запросы текущего клиента."""
    while True:
        header = read_exact(conn, REQ_HEADER_SIZE)
        if not header or len(header) < REQ_HEADER_SIZE:
            break
        opcode, body_len = struct.unpack("<BI", header)
        body_bytes = read_exact(conn, body_len)
        payload = (
            json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        )
        resp_data = handle_request(opcode, payload)
        resp_body = json.dumps(resp_data).encode("utf-8")
        resp_hdr = struct.pack(
            "<BHI", PROTOCOL_VERSION, opcode, len(resp_body)
        )
        conn.sendall(resp_hdr + resp_body)


def start_server():
    """Запускает TCP сервер обработки RPC запросов."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(MAX_CONNECTIONS)

    while True:
        conn, _ = srv.accept()
        try:
            _process_client_connection(conn)
        except Exception as err:
            sys.stdout.write(f"Server Error: {err}\n")
        finally:
            conn.close()


if __name__ == "__main__":
    start_server()