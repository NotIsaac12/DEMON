import os
import sys
import subprocess
import glob
import ctypes
import importlib.util

# =====================================================================
# НОВАЯ МИКРОЯДЕРНАЯ ИНИЦИАЛИЗАЦИЯ ПРОЕКТА
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHELL_DIR = os.path.join(BASE_DIR, 'DemonShell')

# ФИКС: Все папки теперь инкапсулированы внутри DemonShell
DB_DIR = os.path.join(SHELL_DIR, 'Databases')
NOTE_DIR = os.path.join(SHELL_DIR, 'Notes')
DOWNLOADS_DIR = os.path.join(SHELL_DIR, 'Downloads')
MEDIA_DIR = os.path.join(SHELL_DIR, 'GeneratedMedia')
MUSIC_DIR = os.path.join(SHELL_DIR, 'GeneratedMusic')
WORD_DIR = os.path.join(SHELL_DIR, 'Reports', 'Word')
EXCEL_DIR = os.path.join(SHELL_DIR, 'Reports', 'Excel')

# Бункер плагинов остается в корне проекта для удобства деплоя
PLUGINS_DIR = os.path.join(BASE_DIR, 'Plugins')

for folder in [DB_DIR, NOTE_DIR, DOWNLOADS_DIR, MEDIA_DIR, MUSIC_DIR, WORD_DIR, EXCEL_DIR, PLUGINS_DIR]:
    os.makedirs(folder, exist_ok=True)

# =====================================================================
# СИСТЕМНОЕ ЖЕЛЕЗО
# =====================================================================
def auto_install_package(package_name: str, project_name: str = "") -> str:
    try:
        cmd = f'"{sys.executable}" -m pip install {package_name}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='replace')
        return f"Пакет '{package_name}' готов." if res.returncode == 0 else res.stderr
    except Exception as e: return f"Сбой pip: {str(e)}"

def inject_new_native_tool(tool_code: str, tool_name: str) -> str:
    try:
        filename = f"{tool_name}.py" if not tool_name.endswith(".py") else tool_name
        plugin_path = os.path.join(PLUGINS_DIR, filename)
        clean_code = tool_code.replace("```python", "").replace("```", "").strip()
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(clean_code)
        main_file = os.path.join(BASE_DIR, "main.py")
        if os.path.exists(main_file): os.utime(main_file, None)
        return f"🔥 Плагин 'Plugins/{filename}' успешно инкапсулирован."
    except Exception as e: return f"Ошибка эволюции: {str(e)}"

def get_available_tools_list() -> dict:
    data = {"core": [f.__name__ for f in BASE_TOOLS], "plugins": []}
    plugin_files = glob.glob(os.path.join(PLUGINS_DIR, "*.py"))
    for file_path in plugin_files:
        filename = os.path.basename(file_path)
        human_name = filename.replace(".py", "")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#"): human_name = first_line.replace("#", "").strip()
        except: pass
        data["plugins"].append({"file": filename, "name": human_name})
    return data

BASE_TOOLS = [auto_install_package, inject_new_native_tool]

def load_dynamic_plugins():
    registered_tools = list(BASE_TOOLS)
    plugin_files = glob.glob(os.path.join(PLUGINS_DIR, "*.py"))
    for file_path in plugin_files:
        try:
            module_name = os.path.basename(file_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, module_name):
                func_obj = getattr(module, module_name)
                if func_obj not in registered_tools: registered_tools.append(func_obj)
        except: continue
    return registered_tools

ALL_TOOLS = load_dynamic_plugins()
TOOLS_MAP = {f.__name__: f for f in ALL_TOOLS}
