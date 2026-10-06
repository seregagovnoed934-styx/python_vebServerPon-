import pytest
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule
import main as db


class DatabaseMBT(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        # При каждом перезапуске сценария очищаем таблицы, если в main есть сброс, 
        # либо проверяем корректность работы инкремента
        if hasattr(db, "users_table") and isinstance(db.users_table, list):
            db.users_table.clear()
        if hasattr(db, "messages_table") and isinstance(db.messages_table, list):
            db.messages_table.clear()
        if hasattr(db, "completions_table") and isinstance(db.completions_table, list):
            db.completions_table.clear()

    # Бандлы для хранения сгенерированных сущностей
    users = Bundle("users")
    messages = Bundle("messages")

    @rule(target=users, ip=st.ip_addresses().map(str))
    def create_user(self, ip):
        user_id = db.create_user(ip)
        assert user_id is not None
        return user_id

    @rule(target=messages, user_id=users, description=st.text(min_size=1, max_size=30))
    def create_message(self, user_id, description):
        msg_id = db.create_message(description, user_id)
        assert msg_id is not None
        return msg_id

    @rule(state=st.sampled_from(["SUCCESS", "IN_PROGRESS", "RESOLVED", "FAILED"]), message_id=messages)
    def create_completion(self, state, message_id):
        comp_id = db.create_completion(state, message_id)
        assert comp_id is not None

    @rule()
    def verify_get_users(self):
        users = db.get_users()
        assert isinstance(users, list)

    @rule()
    def verify_select(self):
        res = db.select()
        assert isinstance(res, list)


# Экспортируем класс как TestCase для Pytest
TestDatabaseMBT = DatabaseMBT.TestCase