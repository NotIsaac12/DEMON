# Плагин принудительного удаления ИИ-программ
import os


def delete_plugin_app(plugin_name: str) -> str:
    """ Нативно стирает выбранный плагин из папки Plugins/ и очищает конфигурацию. """
    try:
        if not plugin_name.endswith(".py"):
            plugin_name += ".py"

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_path = os.path.join(project_root, "Plugins", plugin_name)

        if not os.path.exists(plugin_path):
            return f"❌ Ошибка: Программа '{plugin_name}' не найдена в папке Plugins/."

        # Принудительно удаляем файл с жесткого диска
        os.remove(plugin_path)

        # Сигнализируем main.py о необходимости мягкой перезагрузки ОЗУ
        main_file = os.path.join(project_root, "main.py")
        if os.path.exists(main_file): os.utime(main_file, None)

        return f"🗑️ ПО '{plugin_name}' успешно уничтожено и стерто из памяти Демона!"
    except Exception as e:
        return f"Ошибка удаления файла: {str(e)}"
