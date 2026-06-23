import sys
import os
import threading
import ctypes
import subprocess
import keyboard
import socket
import json
import re
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QTextEdit, QLabel, QPushButton, QColorDialog, QCheckBox, QComboBox
from PyQt6.QtGui import QColor
from brain import execute_parallel_task
from PIL import Image, ImageDraw
import pystray

PORT = 9999
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt")

def log_exception(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] КРИТИЧЕСКИЙ СБОЙ СИСТЕМЫ:\n{error_msg}\n{'-'*60}\n")
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = log_exception

DEFAULT_CONFIG = {
    "version": "1.0.0",
    "neon_rgb": True,
    "log_color": "#9ece6a",
    "answer_color": "#ffffff",
    "border_color": "#7aa2f7",
    "theme": "dark"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(config, f, indent=4)

if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join([f'"{a}"' for a in sys.argv]), None, 1)
    sys.exit(0)

if "--context" in sys.argv:
    keyboard.send('ctrl+c')
    import time
    time.sleep(0.15)
    ctypes.windll.user32.OpenClipboard(None)
    pcontents = ctypes.windll.user32.GetClipboardData(1)
    text_data = ctypes.c_char_p(pcontents).value.decode('cp1251', errors='ignore').strip() if pcontents else ""
    ctypes.windll.user32.CloseClipboard()
    if text_data:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', PORT))
            client.sendall(text_data.encode('utf-8'))
            client.close()
            sys.exit(0)
        except ConnectionRefusedError: pass
    if "--context" in sys.argv: sys.argv.remove("--context")

class DaemonSignals(QObject):
    f4_pressed = pyqtSignal()
    text_received = pyqtSignal(str, bool)
    remote_query_received = pyqtSignal(str)
    config_changed = pyqtSignal()

signals = DaemonSignals()

ASCII_DEMON_BASE = r"""<pre style="color: #bb9af7; font-family: Consolas, monospace; font-size: 8px; line-height: 1.05; font-weight: bold; margin: 0; text-align: left;">
  _______   ________  __       __   ______   __    __ 

 |       \ |        \|  \     /  \ /      \ |  \  |  \
 | $$$$$$$\| $$$$$$$$| $$\   /  $$|  $$$$$$\| $$\ | $$
 | $$  | $$| $$__    | $$$\ /  $$$| $$  | $$| $$$\ | $$
 | $$  | $$| $$  \   | $$$    $$$$| $$  | $$| $$$$ \ $$
 | $$  | $$| $$$$$   | PRIV \$$ $$| $$  | $$| $$\$$ $$
 | $$__/ $$| $$_____ | $$ \$$$| $$| $$__/ $$| $$ \$$$$
 | $$    $$| $$     \| $$  \$ | $$ \$$    $$| $$  \$$$
  \$$$$$$$  \$$$$$$$$ \$$      \$$  \$$$$$$  \$$   \$$
</pre>
<p style="color: #7aa2f7; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; margin: 10px 0 2px 0; text-shadow: 0 0 2px #7aa2f7;">
  ─────────────────────────────────────────────────────────────<br>
  ⚡ CORE VERSION: {version}<br>
  😈 СТАТУС ЯДРА: ОЖИДАЮ ПРИКАЗОВ В СИСТЕМЕ...<br>
  ─────────────────────────────────────────────────────────────
</p>"""
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(340, 340)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.container = QWidget(self)
        self.container.setStyleSheet("QWidget { background-color: #0f1015; border: 2px solid #7aa2f7; border-radius: 12px; }")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("⚙️ МОДИФИКАЦИЯ СИСТЕМЫ", self)
        title.setStyleSheet("color: #7aa2f7; font-weight: bold; font-size: 12px; border: none;")
        layout.addWidget(title)
        self.cb_neon = QCheckBox(" АКТИВИРОВАТЬ RGB НЕОН")
        self.cb_neon.setChecked(self.cfg.get("neon_rgb", True))
        self.cb_neon.setStyleSheet("QCheckBox { color: #bb9af7; font-weight: bold; font-size: 11px; padding: 5px; } QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #bb9af7; border-radius: 4px; background: #16161e; } QCheckBox::indicator:checked { background: #bb9af7; }")
        self.cb_neon.stateChanged.connect(self.update_preview)
        layout.addWidget(self.cb_neon)
        btn_style = "QPushButton { background-color: #16161e; color: #c0caf5; border: 1px solid #414868; border-radius: 6px; padding: 8px; text-align: left; font-size: 11px; } QPushButton:hover { border: 1px solid #7aa2f7; background: #1a1b26; }"
        self.btn_log = QPushButton("🟩 Цвет технических логов", self)
        self.btn_log.setStyleSheet(btn_style)
        self.btn_log.clicked.connect(lambda: self.pick_color("log_color"))
        layout.addWidget(self.btn_log)
        self.btn_ans = QPushButton("⬜ Цвет ответов и чата", self)
        self.btn_ans.setStyleSheet(btn_style)
        self.btn_ans.clicked.connect(lambda: self.pick_color("answer_color"))
        layout.addWidget(self.btn_ans)
        self.btn_border = QPushButton("🟪 Статичный цвет обводки", self)
        self.btn_border.setStyleSheet(btn_style)
        self.btn_border.clicked.connect(lambda: self.pick_color("border_color"))
        layout.addWidget(self.btn_border)
        layout.addWidget(QLabel("ЖИВОЙ ПРЕДПРОСМОТР СТИЛЯ:"))
        self.preview_box = QTextEdit(self)
        self.preview_box.setReadOnly(True)
        self.preview_box.setFixedHeight(65)
        layout.addWidget(self.preview_box)
        btn_box = QHBoxLayout()
        btn_close = QPushButton("ОТМЕНА", self)
        btn_close.setStyleSheet("QPushButton { background: transparent; color: #f7768e; border: 1px solid #f7768e; border-radius: 6px; padding: 6px; font-weight: bold; } QPushButton:hover { background: #f7768e; color: #0f1015; }")
        btn_close.clicked.connect(self.close)
        btn_box.addWidget(btn_close)
        btn_save = QPushButton("ПРИМЕНИТЬ", self)
        btn_save.setStyleSheet("QPushButton { background: #7aa2f7; color: #0f1015; border-radius: 6px; padding: 6px; font-weight: bold; } QPushButton:hover { background: #89ddff; }")
        btn_save.clicked.connect(self.save_settings)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        self.update_preview()

    def pick_color(self, key):
        color = QColorDialog.getColor(QColor(self.cfg[key]), self, "Выбор цвета")
        if color.isValid():
            self.cfg[key] = color.name()
            self.update_preview()

    def update_preview(self):
        border = self.cfg.get("border_color", "#7aa2f7")
        self.preview_box.setStyleSheet(f"background-color: #16161e; border: 1px solid {border}; border-radius: 4px; padding: 4px;")
        html = f'<p style="color: {self.cfg.get("log_color")}; font-size: 10px; font-family: Consolas; margin:0;">⚙️ Слой: выполнение...</p>'
        html += f'<p style="color: {self.cfg.get("answer_color")}; font-size: 12px; font-family: Segoe UI; font-weight: bold; margin:2px 0;">Финальный ответ Демона</p>'
        self.preview_box.setHtml(html)

    def save_settings(self):
        self.cfg["neon_rgb"] = self.cb_neon.isChecked()
        save_config(self.cfg)
        signals.config_changed.emit()
        self.close()
class PluginsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(380, 400)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        container = QWidget(self)
        container.setStyleSheet("QWidget { background-color: #0f1015; border: 2px solid #bb9af7; border-radius: 12px; }")
        layout = QVBoxLayout(container)
        title = QLabel("📋 КАТАЛОГ ПОДКЛЮЧЕННЫХ ИИ-ПЛАГИНОВ", self)
        title.setStyleSheet("color: #bb9af7; font-weight: bold; font-size: 11px; border: none; margin-bottom: 5px;")
        layout.addWidget(title)
        self.area = QTextEdit(self)
        self.area.setReadOnly(True)
        self.area.setStyleSheet("QTextEdit { background-color: #16161e; border: 1px solid #414868; border-radius: 6px; color: #ffffff; }")
        layout.addWidget(self.area)
        btn_close = QPushButton("ЗАКРЫТЬ", self)
        btn_close.setStyleSheet("QPushButton { background: #bb9af7; color: #0f1015; border-radius: 6px; padding: 6px; font-weight: bold; } QPushButton:hover { background: #7aa2f7; }")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        self.refresh_list()

    def refresh_list(self):
        from tools import get_available_tools_list
        data = get_available_tools_list()
        html = '<b style="color: #7aa2f7; font-size: 12px;">⚡ НЕУБИВАЕМОЕ СИСТЕМНОЕ ЯДРО:</b><br>'
        for c in data["core"]: html += f'<span style="color: #9ece6a; font-family: Consolas;">• {c}</span><br>'
        html += '<br><b style="color: #bb9af7; font-size: 12px;">😈 АКТИВНЫЕ ИИ-ПЛАГИНЫ:</b><br>'
        if not data["plugins"]:
            html += '<i style="color: #565f89;">Список пуст. Плагины не обнаружены.</i>'
        for p in data["plugins"]:
            html += f'<b style="color: #ffffff;">• {p["name"]}</b> <i style="color: #565f89; font-size: 10px;">({p["file"]})</i><br>'
        self.area.setHtml(html)


class CyberpunkTerminalUI(QWidget):
    def __init__(self):
        super().__init__()
        self.is_visible, self.drag_resizing, self.first_request_done, self.task_counter = False, False, False, 0
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.rgb_phase = 0
        self.typing_queue, self.current_typing_text, self.current_typing_index, self.current_is_technical = [], "", 0, False

        self.init_ui()
        self.apply_current_config()

        signals.f4_pressed.connect(self.toggle_slide)
        signals.text_received.connect(self.queue_text_for_typing)
        signals.remote_query_received.connect(self.handle_remote_query)
        signals.config_changed.connect(self.apply_current_config)

        self.rgb_timer = QTimer(self)
        self.rgb_timer.timeout.connect(self.update_rgb_neon)
        self.rgb_timer.start(70)

        self.typewriter_timer = QTimer(self)
        self.typewriter_timer.timeout.connect(self.process_typewriter_tick)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(550, 440)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget(self)
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(15, 12, 15, 15)
        top_bar = QHBoxLayout()
        self.status_label = QLabel("😈 DEMONSHELL CORE", self)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        self.btn_plugins = QPushButton("📋", self)
        self.btn_plugins.setFixedSize(26, 26)
        self.btn_plugins.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_plugins.clicked.connect(self.open_plugins_window)
        top_bar.addWidget(self.btn_plugins)
        self.btn_settings = QPushButton("⚙️", self)
        self.btn_settings.setFixedSize(26, 26)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings)
        top_bar.addWidget(self.btn_settings)
        c_layout.addLayout(top_bar)
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Прикажи мне... (F4)")
        self.input_field.returnPressed.connect(self.send_to_brain)
        c_layout.addWidget(self.input_field)
        self.terminal_area = QTextEdit(self)
        self.terminal_area.setReadOnly(True)
        c_layout.addWidget(self.terminal_area)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        self.update_positions()
        self.move(self.hide_pos)

    def apply_current_config(self):
        cfg = load_config()
        border = cfg.get("border_color", "#7aa2f7")
        bg, inner_bg, text = "#0f1015", "#16161e", "#c0caf5"
        self.container.setStyleSheet(
            f"QWidget {{ background-color: {bg}; border: 2px solid {border}; border-radius: 14px; }}")
        self.status_label.setStyleSheet(
            f"color: {border}; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        btn_style = f"QPushButton {{ background: transparent; color: {border}; border: 1px solid {border}; border-radius: 6px; font-size: 11px; font-weight: bold; }} QPushButton:hover {{ background: {border}; color: {bg}; }}"
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_plugins.setStyleSheet(btn_style)
        self.input_field.setStyleSheet(
            f"QLineEdit {{ background-color: {inner_bg}; color: {text}; border: 1px solid {border}; border-radius: 6px; padding: 8px; font-size: 12px; font-family: 'Segoe UI'; }}")
        self.terminal_area.setStyleSheet(
            f"QTextEdit {{ background-color: {inner_bg}; border: 1px solid {border}; border-radius: 6px; padding: 10px; color: {text}; }}")
        if not self.first_request_done:
            self.terminal_area.setHtml(ASCII_DEMON_BASE.format(version=cfg.get("version", "1.0.0")))

    def update_rgb_neon(self):
        cfg = load_config()
        if not cfg.get("neon_rgb", True) or not self.is_visible: return
        self.rgb_phase = (self.rgb_phase + 4) % 360
        hex_color = QColor.fromHsv(self.rgb_phase, 210, 240).name()
        try:
            self.container.setStyleSheet(
                re.sub(r"border: 2px solid #\w+;", f"border: 2px solid {hex_color};", self.container.styleSheet()))
            self.status_label.setStyleSheet(
                f"color: {hex_color}; font-weight: bold; font-size: 11px; border: none; background: transparent;")
            self.btn_settings.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {hex_color}; border: 1px solid {hex_color}; border-radius: 6px; font-size: 11px; font-weight: bold; }} QPushButton:hover {{ background: {hex_color}; color: #0f1015; }}")
            self.btn_plugins.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {hex_color}; border: 1px solid {hex_color}; border-radius: 6px; font-size: 11px; font-weight: bold; }} QPushButton:hover {{ background: {hex_color}; color: #0f1015; }}")
        except:
            pass

    def toggle_slide(self):
        self.update_positions()
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        if not self.is_visible:
            self.show();
            self.raise_();
            self.anim.setStartValue(self.pos());
            self.anim.setEndValue(self.show_pos);
            self.anim.start()
            self.is_visible = True;
            self.activateWindow();
            self.input_field.setFocus()
        else:
            self.anim.setStartValue(self.pos());
            self.anim.setEndValue(self.hide_pos);
            self.anim.finished.connect(self.hide);
            self.anim.start()
            self.is_visible = False

    def open_plugins_window(self):
        self.plugins_win = PluginsWindow()
        self.plugins_win.show()

    def queue_text_for_typing(self, text, is_technical):
        if not self.first_request_done: self.terminal_area.clear(); self.first_request_done = True
        self.typing_queue.append((text, is_technical))
        if not self.typewriter_timer.isActive(): self.start_next_line_typing()

    def start_next_line_typing(self):
        if not self.typing_queue: self.typewriter_timer.stop(); return
        self.current_typing_text, self.current_is_technical = self.typing_queue.pop(0)
        self.current_typing_index = 0
        self.terminal_area.append("")
        speed = 5 if self.current_is_technical else 12
        self.typewriter_timer.start(speed)

    def process_typewriter_tick(self):
        if self.current_typing_index < len(self.current_typing_text):
            self.current_typing_index += 1
            raw_partial = self.current_typing_text[:self.current_typing_index]

            # БРОНЯ: Экранируем спецсимволы ошибок, чтобы они не ломали Html-движок PyQt6
            partial_text = raw_partial.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            cfg = load_config()
            if self.current_is_technical:
                html = f'<span style="color: {cfg.get("log_color")}; font-size: 11px; font-family: Consolas, monospace;">{partial_text}</span>'
            else:
                html = f'<p style="color: {cfg.get("answer_color")}; font-size: 13px; font-weight: bold; font-family: \'Segoe UI\';">{partial_text}</p>'
                if not self.is_visible: self.toggle_slide()
            cursor = self.terminal_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText();
            cursor.insertHtml(html)
            self.terminal_area.verticalScrollBar().setValue(self.terminal_area.verticalScrollBar().maximum())
        else:
            self.start_next_line_typing()

    def open_settings(self):
        self.settings_win = SettingsWindow()
        self.settings_win.show()

    def update_positions(self):
        screen_geo = QApplication.primaryScreen().geometry()
        self.hide_pos = QPoint(25, screen_geo.height())
        self.show_pos = QPoint(25, screen_geo.height() - self.height() - 50)

    def mousePressEvent(self, event):
        if event.position().y() <= 20:
            self.drag_resizing, self.drag_start_y, self.drag_start_height = True, event.globalPosition().y(), self.height()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_resizing:
            delta_y = event.globalPosition().y() - self.drag_start_y
            new_height = max(240, int(self.drag_start_height - delta_y))
            self.setGeometry(self.x(), QApplication.primaryScreen().geometry().height() - new_height - 50, self.width(),
                             new_height)
            self.update_positions();
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_resizing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.toggle_slide()
        else:
            super().keyPressEvent(event)

    def dispatch_new_task(self, query: str):
        if not self.first_request_done: self.terminal_area.clear(); self.first_request_done = True
        self.task_counter += 1
        self.queue_text_for_typing(f"🚀 [Поток #{self.task_counter}] Запрос: {query}", False)
        self.thread_pool.submit(execute_parallel_task, query, signals.text_received.emit, self.task_counter)

    def handle_remote_query(self, query):
        if not self.is_visible: self.toggle_slide()
        self.dispatch_new_task(query)

    def send_to_brain(self):
        query = self.input_field.text().strip()
        if not query: return
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        self.dispatch_new_task(query)


def start_local_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('127.0.0.1', PORT));
        server.listen(5)
        while True:
            conn, addr = server.accept()
            data = conn.recv(4096).decode('utf-8', errors='ignore').strip()
            if data: signals.remote_query_received.emit(data)
            conn.close()
    except:
        pass


def install_daemon_into_windows():
    args_list = sys.argv
    target_script = args_list[0] if len(args_list) > 0 else __file__
    script_path = os.path.abspath(target_script)
    current_python = sys.executable
    pythonw_exe = current_python.lower().replace("python.exe", "pythonw.exe") if current_python.lower().endswith(
        "python.exe") else current_python
    run_cmd = f'"{pythonw_exe}" "{script_path}"'
    task_name = "DemonShell_Core_Autostart"
    subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, capture_output=True)
    subprocess.run(
        f'schtasks /create /tn "{task_name}" /tr "{run_cmd.replace("\"", "\\\"")}" /sc ONLOGON /rl HIGHEST /f',
        shell=True, capture_output=True)
    import winreg
    for path in [r"Directory\Background\shell\DemonShell", r"*\shell\DemonShell"]:
        try:
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, path)
            winreg.SetValue(key, "", winreg.REG_SZ, "😈 Спросить Демона")
            winreg.SetValue(winreg.CreateKey(key, "command"), "", winreg.REG_SZ, f'{run_cmd} --context')
        except:
            pass


if __name__ == "__main__":
    install_daemon_into_windows()
    app = QApplication(sys.argv)
    ui = CyberpunkTerminalUI()
    keyboard.add_hotkey('F4', lambda: signals.f4_pressed.emit())
    threading.Thread(target=start_local_socket_server, daemon=True).start()


    def run_tray():
        img = Image.new('RGB', (64, 64), color='#16161e')
        ImageDraw.Draw(img).text((20, 20), "😈", fill="#bb9af7")
        icon = pystray.Icon("DemonShell", img, "😈 DEMON OS", menu=pystray.Menu(
            pystray.MenuItem("Развернуть консоль [F4]", lambda: signals.f4_pressed.emit()),
            pystray.MenuItem("Выход из ПО", lambda i, item: [i.stop(), QApplication.quit(), os._exit(0)])
        ))
        icon.run()


    threading.Thread(target=run_tray, daemon=True).start()
    timer = QTimer();
    timer.timeout.connect(lambda: None);
    timer.start(50)
    sys.exit(app.exec())
