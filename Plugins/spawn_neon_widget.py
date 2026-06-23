# Фабрика Неоновых Виджетов Демона
import os
import sys
import subprocess


def spawn_neon_widget(widget_name: str, widget_html_code: str) -> str:
    """На лету собирает и выводит на рабочий стол скрытое асинхронное неоновое окно-виджет."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        widgets_folder = os.path.join(base_dir, "DemonShell", "Widgets")
        os.makedirs(widgets_folder, exist_ok=True)  # АВТОСОЗДАНИЕ ПАПКИ ВНУТРИ SHELL

        # Генерируем независимый исполняемый скрипт для окна PyQt6
        widget_script_code = f"""import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit

app = QApplication(sys.argv)
win = QWidget()
win.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
win.resize(260, 160)

layout = QVBoxLayout()
layout.setContentsMargins(0,0,0,0)
box = QTextEdit()
box.setReadOnly(True)
box.setStyleSheet("background-color: #0f1015; border: 2px solid #7aa2f7; border-radius: 12px; color: #ffffff; padding: 10px;")
box.setHtml('''{widget_html_code}''')

layout.addWidget(box)
win.setLayout(layout)
win.show()
sys.exit(app.exec())
"""
        widget_path = os.path.join(widgets_folder, f"{widget_name}.py")
        with open(widget_path, "w", encoding="utf-8") as f:
            f.write(widget_script_code)

        # Запускаем созданное окно асинхронно в фоне Windows, чтобы оно жило своей жизнью
        subprocess.Popen(f'"{sys.executable}" "{widget_path}"', shell=True)
        return f"🔥 Виджет '{widget_name}' успешно скомпилирован в ОЗУ и выведен на рабочий стол!"
    except Exception as e:
        return f"Ошибка компиляции окна виджета: {str(e)}"
