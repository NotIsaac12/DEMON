# Плагин создания изолированных Python проектов
import os
import sys
import subprocess


def create_python_project(project_name: str, main_code: str) -> str:
    """Создает независимую папку проекта в DemonShell/Projects/, разворачивает .venv и пишет main.py."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proj_dir = os.path.join(base_dir, "DemonShell", "Projects", project_name)

        # АВТОНОМНОЕ РАЗВЕРТЫВАНИЕ ДИРЕКТОРИИ
        os.makedirs(proj_dir, exist_ok=True)

        # Создаем venv
        venv_dir = os.path.join(proj_dir, ".venv")
        if not os.path.exists(venv_dir):
            subprocess.run(f'"{sys.executable}" -m venv "{venv_dir}"', shell=True, capture_output=True)

        # Записываем исходный код
        main_path = os.path.join(proj_dir, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_code)

        return f"✅ Проект '{project_name}' успешно создан в DemonShell/Projects/ с изолированным окружением .venv"
    except Exception as e:
        return f"Ошибка создания проекта: {str(e)}"
