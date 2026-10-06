"""Модуль работы с ин-мемори хранилищем данных."""

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


def _find_message(m_id: int):
    """Вспомогательная функция поиска сообщения по ID."""
    for msg in messages_table:
        if msg[0] == m_id:
            return msg
    return None


def _find_user(u_id: int):
    """Вспомогательная функция поиска пользователя по ID."""
    for usr in users_table:
        if usr[0] == u_id:
            return usr
    return None


def _join_single_comp(comp, now, matched_msgs, matched_usrs):
    """Обрабатывает одну запись статуса."""
    c_state, m_id = comp[1], comp[2]
    msg = _find_message(m_id)
    if not msg:
        return None
    m_desc, m_time, u_id = msg[1], msg[2], msg[3]
    if now - m_time > TIME_WINDOW_SECONDS:
        return None
    matched_msgs.add(m_id)
    usr = _find_user(u_id)
    if usr:
        matched_usrs.add(u_id)
        return (c_state, m_desc, usr[1])
    return (c_state, m_desc, None)


def _process_completions(now, matched_msgs, matched_usrs):
    """Обрабатывает слияние по таблице статусов."""
    res = []
    for comp in completions_table:
        item = _join_single_comp(comp, now, matched_msgs, matched_usrs)
        if item:
            res.append(item)
    return res


def _join_single_msg(msg, now, matched_msgs, matched_usrs):
    """Обрабатывает одно несовпавшее сообщение."""
    m_id, m_desc, m_time, u_id = msg[0], msg[1], msg[2], msg[3]
    if m_id in matched_msgs or (now - m_time > TIME_WINDOW_SECONDS):
        return None
    usr = _find_user(u_id)
    if usr:
        matched_usrs.add(u_id)
        return (None, m_desc, usr[1])
    return (None, m_desc, None)


def _process_unmatched_msgs(now, matched_msgs, matched_usrs):
    """Обрабатывает несовпавшие сообщения."""
    res = []
    for msg in messages_table:
        item = _join_single_msg(msg, now, matched_msgs, matched_usrs)
        if item:
            res.append(item)
    return res


def _process_unmatched_usrs(matched_usrs):
    """Обрабатывает несовпавших пользователей."""
    res = []
    for usr in users_table:
        u_id, u_ip = usr[0], usr[1]
        if u_id not in matched_usrs:
            res.append((None, None, u_ip))
    return res


def select():
    """Выполняет выборку Full Outer Join с фильтром по времени."""
    now = time.time()
    matched_msgs = set()
    matched_usrs = set()

    part1 = _process_completions(now, matched_msgs, matched_usrs)
    part2 = _process_unmatched_msgs(now, matched_msgs, matched_usrs)
    part3 = _process_unmatched_usrs(matched_usrs)

    return part1 + part2 + part3



