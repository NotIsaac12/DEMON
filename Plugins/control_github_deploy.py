# Локальный плагин контроля версий и бэкапа ядра DEMON
import os
import subprocess
import json


def control_github_deploy(new_version: str, commit_message: str = "Локальное обновление системы") -> str:
    """
    По твоему приказу делает моментальный снимок (бэкап) всей системы DEMON.
    Сохраняет историю изменений в локальный Git без отправки файлов в интернет.
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.json")

        # 1. ОБНОВЛЕНИЕ ЛОКАЛЬНОГО КОНФИГА
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        else:
            config_data = {"theme": "dark"}

        old_version = config_data.get("version", "1.0.0")
        ai_name = config_data.get("ai_model", "Qwen-2.5-7B-Instruct")

        # Записываем новую локальную версию в JSON
        config_data["version"] = new_version
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        # 2. МОМЕНТАЛЬНЫЙ СНИМОК В ЛОКАЛЬНЫЙ GIT (БЕЗ ИНТЕРНЕТА)
        git_commands = [
            f'git -C "{project_root}" init',  # Проверяем, что локальный гид активен
            f'git -C "{project_root}" add .',  # Индексируем все новые плагины
            f'git -C "{project_root}" commit -m "🤖 [{ai_name}] {commit_message} v{new_version}"'
            # Фиксируем срез в историю
        ]

        for cmd in git_commands:
            subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='replace')

        return f"💾 БЭКАП ЗАВЕРШЕН СУПЕРБЫСТРО!\nЛокальная версия повышена с {old_version} до v{new_version}.\n✅ Все изменения зафиксированы в скрытом локальном хранилище .git/"

    except Exception as e:
        return f"Ошибка локального бэкапа: {str(e)}"
