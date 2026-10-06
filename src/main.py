import time

# Слой хранения данных (таблицы)
users = []
messages = []
completions = []


def create_user(ip: str) -> int:
    return create(users, ip)


def create_message(description: str, user_id: int) -> int:
    return create(messages, description, user_id)


def create_completion(state: str, message_id: int) -> int:
    return create(completions, state, message_id)


def create(table: list, *args) -> int:
    id = len(table)
    timestamp = int(time.time())
    # Согласно требованиям 15 варианта, записи хранятся в виде кортежей (tuples)
    table.append((id, timestamp, *args))
    return id


def get_users():
    return users


def get_messages():
    return messages


def get_completions():
    return completions


def find_user_by_id(id: int):
    if id < len(users):
        return users[id]


def find_message_by_id(id: int):
    if id < len(messages):
        return messages[id]


def find_completion_by_id(id: int):
    if id < len(completions):
        return completions[id]


def select():
    # Фильтрация сообщений: старше (now - 9 min)
    # 9 минут = 540 секунд
    offset = int(time.time()) - 540
    
    # Создаем отфильтрованный список сообщений, удовлетворяющих условию времени
    valid_messages = [m for m in messages if m[1] > offset]
    
    output = []
    
    # Множества для отслеживания связей (чтобы реализовать Full Outer Join)
    matched_u = set()
    matched_m = set()
    matched_c = set()
    
    # 1. Ищем пересечения Users и Messages
    for u in users:
        for m in valid_messages:
            if u[0] == m[3]:  # user.id == message.user_id
                match_c_found = False
                for c in completions:
                    if c[3] == m[0]:  # completion.message_id == message.id
                        # Проекция: C.state, M.description, U.ip
                        output.append((c[2], m[2], u[2]))
                        matched_u.add(u[0])
                        matched_m.add(m[0])
                        matched_c.add(c[0])
                        match_c_found = True
                
                # Если у сообщения нет Completion
                if not match_c_found:
                    output.append((None, m[2], u[2]))
                    matched_u.add(u[0])
                    matched_m.add(m[0])

    # 2. Ищем Messages без привязки к Users, но возможно с привязкой к Completions
    for m in valid_messages:
        if m[0] not in matched_m:
            match_c_found = False
            for c in completions:
                if c[3] == m[0]:
                    output.append((c[2], m[2], None))
                    matched_m.add(m[0])
                    matched_c.add(c[0])
                    match_c_found = True
            
            # Если сообщение висит вообще без связей
            if not match_c_found:
                output.append((None, m[2], None))
                matched_m.add(m[0])

    # 3. Добавляем "осиротевшие" записи Users (Full Outer Join)
    for u in users:
        if u[0] not in matched_u:
            output.append((None, None, u[2]))
            
    # 4. Добавляем "осиротевшие" записи Completions (Full Outer Join)
    for c in completions:
        if c[0] not in matched_c:
            output.append((c[2], None, None))

    return output


def repl():
    print("REPL запущен. Доступные команды: create_user, create_message, create_completion, get_users, get_messages, get_completions, select")
    while True:
        try:
            user_command = input("\n> ").strip()
            match user_command:
                case "create_user":
                    ip = input("Введите IP пользователя (str): ")
                    print(f"Успешно. ID: {create_user(ip)}")
                
                case "create_message":
                    desc = input("Введите описание (str): ")
                    u_id = int(input("Введите ID пользователя (int): "))
                    print(f"Успешно. ID: {create_message(desc, u_id)}")
                    
                case "create_completion":
                    state = input("Введите статус (str): ")
                    m_id = int(input("Введите ID сообщения (int): "))
                    print(f"Успешно. ID: {create_completion(state, m_id)}")
                    
                case "get_users":
                    print(get_users())
                    
                case "get_messages":
                    print(get_messages())
                    
                case "get_completions":
                    print(get_completions())
                    
                case "select":
                    result = select()
                    print("\nРезультат сложной выборки (C.state, M.description, U.ip):")
                    for row in result:
                        print(row)
                        
                case "exit" | "quit":
                    break
                    
                case _:
                    print("Неизвестная команда.")
        except ValueError:
            print("Ошибка: ожидалось числовое значение для ID.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


if __name__ == "__main__":  # pragma: no cover
    # Тестовые данные для демонстрации
    u0 = create_user("192.168.0.1")
    u1 = create_user("10.0.0.5")
    
    m0 = create_message("Ошибка базы данных", u0)
    m1 = create_message("Неверный пароль", u1)
    m2 = create_message("Таймаут соединения", 999) # Сообщение без существующего юзера
    
    c0 = create_completion("RESOLVED", m0)
    c1 = create_completion("IN_PROGRESS", 999) # Завершение без существующего сообщения
    
    print("Начальная выборка:")
    print(select())
    
    # Запуск интерактивного режима
    repl()  # pragma: no cover