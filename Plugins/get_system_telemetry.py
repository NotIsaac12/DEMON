# Телеметрия датчиков железа
import psutil
def get_system_telemetry() -> str:
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    return f"CPU: {cpu}% | RAM: {ram}%"
