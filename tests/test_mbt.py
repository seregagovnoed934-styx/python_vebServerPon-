"""Модуль генеративного тестирования на основе моделей (MBT)."""

import sys
from pathlib import Path

from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src import main as db  # noqa: E402


class DatabaseMBT(RuleBasedStateMachine):
    """Стейт-машина тестирования базы данных."""

    def __init__(self):
        super().__init__()
        db.users_table.clear()
        db.messages_table.clear()
        db.completions_table.clear()

    users = Bundle("users")
    messages = Bundle("messages")

    @rule(target=users, ip=st.ip_addresses().map(str))
    def create_user(self, ip):
        """Тест генерации пользователя."""
        user_id = db.create_user(ip)
        assert user_id is not None
        return user_id

    @rule(
        target=messages,
        user_id=users,
        description=st.text(min_size=1, max_size=20),
    )
    def create_message(self, user_id, description):
        """Тест генерации сообщения."""
        msg_id = db.create_message(description, user_id)
        assert msg_id is not None
        return msg_id

    @rule(
        state=st.sampled_from(["SUCCESS", "RESOLVED", "FAILED"]),
        message_id=messages,
    )
    def create_completion(self, state, message_id):
        """Тест генерации статуса."""
        comp_id = db.create_completion(state, message_id)
        assert comp_id is not None

    @rule()
    def verify_select(self):
        """Тест выборки данных."""
        res = db.select()
        assert isinstance(res, list)


TestDatabaseMBT = DatabaseMBT.TestCase