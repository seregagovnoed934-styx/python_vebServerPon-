import time

TIME_WINDOW_SECONDS = 540

users_table = []
messages_table = []
completions_table = []

_user_id_seq = 1
_message_id_seq = 1
_completion_id_seq = 1


def create_user(ip: str) -> int:
    """Создает пользователя и возвращает его идентификатор."""
    global _user_id_seq
    record = (_user_id_seq, ip)
    users_table.append(record)
    _user_id_seq += 1
    return record[0]


def create_message(description: str, user_id: int) -> int:
    """Создает сообщение со штампом времени."""
    global _message_id_seq
    created_at = time.time()
    record = (_message_id_seq, description, created_at, user_id)
    messages_table.append(record)
    _message_id_seq += 1
    return record[0]


def create_completion(state: str, message_id: int) -> int:
    """Создает статус выполнения сообщения."""
    global _completion_id_seq
    record = (_completion_id_seq, state, message_id)
    completions_table.append(record)
    _completion_id_seq += 1
    return record[0]


def get_users():
    """Возвращает список всех пользователей."""
    return users_table


def get_messages():
    """Возвращает список всех сообщений."""
    return messages_table


def get_completions():
    """Возвращает список всех статусов."""
    return completions_table


def select():
    """Выполняет выборку Full Outer Join с временным фильтром."""
    now = time.time()
    result = []
    matched_messages = set()
    matched_users = set()

    for comp in completions_table:
        c_state, m_id = comp[1], comp[2]
        msg = next((m for m in messages_table if m[0] == m_id), None)
        if msg:
            m_desc, m_time, u_id = msg[1], msg[2], msg[3]
            if now - m_time <= TIME_WINDOW_SECONDS:
                matched_messages.add(m_id)
                usr = next((u for u in users_table if u[0] == u_id), None)
                if usr:
                    matched_users.add(u_id)
                    result.append((c_state, m_desc, usr[1]))
                else:
                    result.append((c_state, m_desc, None))

    for msg in messages_table:
        m_id, m_desc, m_time, u_id = msg[0], msg[1], msg[2], msg[3]
        if m_id not in matched_messages:
            if now - m_time <= TIME_WINDOW_SECONDS:
                usr = next((u for u in users_table if u[0] == u_id), None)
                if usr:
                    matched_users.add(u_id)
                    result.append((None, m_desc, usr[1]))
                else:
                    result.append((None, m_desc, None))

    for usr in users_table:
        u_id, u_ip = usr[0], usr[1]
        if u_id not in matched_users:
            result.append((None, None, u_ip))

    return result