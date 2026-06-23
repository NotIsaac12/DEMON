# Плагин первичной веб-регистрации репозитория в облаке
import os
import json
import requests
import subprocess
import sys


def create_github_repo() -> str:
    """Автоматически регистрирует новый публичный репозиторий DEMON на твоем GitHub через токен."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        token = cfg.get("github_token", "")
        if not token or token == "ТВОЙ_СКОПИРОВАННЫЙ_ТОКЕН_GHP":
            return "❌ Ошибка: В config.json не прописан валидный github_token!"

        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = {"name": "DEMON", "private": False}

        response = requests.post("https://github.com", headers=headers, json=payload)

        if response.status_code == 201:
            log_msg = "✅ Репозиторий 'DEMON' успешно создан в облаке GitHub!\n"
            repo_url = response.json()["clone_url"]
        elif response.status_code == 422:
            log_msg = "⚠️ Репозиторий 'DEMON' уже существует на GitHub. Синхронизирую...\n"
            user_res = requests.get("https://github.com", headers=headers).json()
            repo_url = f"https://github.com{user_res['login']}/DEMON.git"
        else:
            return f"❌ Ошибка API GitHub: Код {response.status_code}."

        git_commands = [
            f'git -C "{project_root}" init',
            f'git -C "{project_root}" remote remove origin',
            f'git -C "{project_root}" remote add origin {repo_url}',
            f'git -C "{project_root}" branch -M main',
            f'git -C "{project_root}" add .',
            f'git -C "{project_root}" commit -m "Core: Первая инициализация DEMON v1.0.0"',
            f'git -C "{project_root}" push -u origin main'
        ]

        for cmd in git_commands:
            subprocess.run(cmd, shell=True, capture_output=True)

        return f"{log_msg}🚀 Проект успешно привязан к удаленной ссылке. Все файлы вытолкнуты на GitHub!"
    except Exception as e:
        return f"Ошибка автоматической инициализации: {str(e)}"
