import json
import ollama
import re
import uuid
from tools import ALL_TOOLS, TOOLS_MAP


def extract_and_execute_fallback(content: str, text_signal_emit, task_id_str: str) -> bool:
    """Перехватывает блоки кода, если модель ушла в текст."""
    executed = False
    sql_blocks = re.findall(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
    if sql_blocks:
        text_signal_emit(f"⚠️ {task_id_str} [Fallback] Обнаружен SQL в тексте. Выполняю...", True)
        result = TOOLS_MAP['execute_sql_commands'](sql_statements=";".join(sql_blocks),
                                                   db_name=f"auto_{uuid.uuid4().hex[:6]}.db")
        text_signal_emit(f"✅ {task_id_str} {result}", True)
        executed = True

    code_blocks = re.findall(r'```(?:python|js|javascript|powershell|batch|bat)\s*(.*?)\s*```', content, re.DOTALL)
    if code_blocks:
        text_signal_emit(f"⚠️ {task_id_str} [Fallback] Обнаружен код. Запускаю компилятор...", True)
        result = TOOLS_MAP['write_and_execute_script'](
            language='python', code_content="\n".join(code_blocks), project_name=f'auto_project_{uuid.uuid4().hex[:6]}',
            file_name='main.py'
        )
        text_signal_emit(f"✅ {task_id_str} {result}", True)
        executed = True

    return executed


def is_query_demanding_action(query: str) -> bool:
    """Определяет, требует ли запрос физического создания/удаления файлов."""
    action_keywords = ["создай", "напиши", "код", "внедрить", "разработай", "запрограммируй", "удали", "сотри",
                       "уничтожь"]
    return any(word in query.lower() for word in action_keywords)


def execute_parallel_task(user_query: str, text_signal_emit, task_num: int):
    """Изолированный поток выполнения ИИ-автоматизации."""
    task_id_str = f"[Поток #{task_num}]"
    text_signal_emit(f"😈 {task_id_str} Демон принял параллельный приказ...", True)

    cleaned_query = re.sub(r'\b(в\s+)?2025|2026(году|года)?\b', '', user_query, flags=re.IGNORECASE).strip()

    # Сканируем установленные плагины
    from tools import get_available_tools_list
    current_tools = get_available_tools_list()
    functions_installed = [p["file"].replace(".py", "") for p in current_tools["plugins"]]

    task_messages = [
        {
            'role': 'system',
            'content': (
                f"Ты — ультимативный ИИ-оркестратор Демон Windows ОС с микроядерной архитектурой.\n\n"
                f"СПИСОК УЖЕ СУЩЕСТВУЮЩИХ ПЛАГИНОВ В СИСТЕМЕ: {functions_installed}\n\n"
                f"ПРАВИЛО МГНОВЕННОГО ЗАПУСКА (0.1 сек):\n"
                f"Если пользователь просит запустить, открыть или показать ЛЮБОЙ визуальный гаджет, виджет или программу, "
                f"и этот плагин УЖЕ ЕСТЬ в списке выше, тебе КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать код или создавать файлы. "
                f"Ты обязан МГНОВЕННО вызвать инструмент 'launch_plugin_app', передав туда имя файла (например, 'get_weather.py').\n\n"
                f"ПРАВИЛО ЭВОЛЮЦИИ (СОЗДАНИЕ НОВОГО):\n"
                f"Если пользователь просит создать что-то новое, чего НЕТ в списке установленных плагинов, ты просто вызываешь "
                f"инструмент 'inject_new_native_tool' и сохраняешь автономный графический код на PyQt6 в папку Plugins/. "
                f"Сделать локальный бэкап, снимок системы или сохранить текущую гит-версию — 'control_github_deploy'.\n"
                f"При создании всегда пиши человеческое имя в самую первую строку кода через знак комментария #.\n\n"
                f"ПРАВИЛО ДЕСТРУКЦИИ (УДАЛЕНИЯ):\n"
                f"Если пользователь просит удалить плагин (например: 'удали кликер'), ты вызываешь инструмент 'delete_plugin_app'.\n\n"
                f"ПРАВИЛО ПРЕЗЕНТАЦИИ НАВЫКОВ:\n"
                f"Если пользователь спрашивает, что ты умеешь делать, ты ЗАПРЕЩАЕШЬ себе писать список текстом. Ты обязан "
                f"вызвать инструмент 'get_available_tools_list', интерфейс сам откроет графическое окно со списком.\n\n"
                f"Запрещено симулировать работу текстом. Всегда доводи дело до вызова реального инструмента."
            )
        },
        {'role': 'user', 'content': cleaned_query}
    ]

    for step in range(7):
        try:
            response = ollama.chat(model='qwen2.5:7b', messages=task_messages, tools=ALL_TOOLS)
            content = response['message'].get('content', '')
            tool_calls = response['message'].get('tool_calls', [])
            task_messages.append(response['message'])

            if not tool_calls:
                if is_query_demanding_action(user_query) and step == 0:
                    fallback_success = extract_and_execute_fallback(content, text_signal_emit, task_id_str)
                    if fallback_success:
                        text_signal_emit(f"🎉 {task_id_str} Перехваченный markdown-код успешно выполнен!", False)
                        break
                    text_signal_emit(f"⚠️ {task_id_str} Попытка уклонения в текст. Корректирую...", True)
                    task_messages.append(
                        {'role': 'user', 'content': "Ошибка: Немедленно вызови функцию (tool) из списка доступных!"})
                    continue
                else:
                    text_signal_emit(content if content else "🎉 Задача успешно обработана локальным ядром!", False)
                break

            for tool in tool_calls:
                name = tool['function']['name']
                args = tool['function']['arguments']

                text_signal_emit(f"⚙️ {task_id_str} Слой автоматизации: {name}...", True)

                if name in TOOLS_MAP:
                    execution_result = TOOLS_MAP[name](**args)
                    if "Ошибка" in execution_result or "ERROR" in execution_result or "❌" in execution_result:
                        text_signal_emit(f"❌ {task_id_str} Сбой: {execution_result}", True)
                        return

                    text_signal_emit(f"✅ {task_id_str} {execution_result}", True)
                    task_messages.append({'role': 'tool', 'name': name, 'content': execution_result})
                else:
                    task_messages.append({'role': 'tool', 'name': name, 'content': "Ошибка: Инструмент не найден."})

        except Exception as e:
            text_signal_emit(f"❌ {task_id_str} Критическая ошибка: {str(e)}", True)
            break
