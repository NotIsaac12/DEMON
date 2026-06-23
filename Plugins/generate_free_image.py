# Плагин ИИ-генерации картинок
import os
import time
import requests


def generate_free_image(prompt: str) -> str:
    """Генерирует арты и текстуры по промпту. Автоматически разворачивает папку GeneratedMedia."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.join(base_dir, "DemonShell", "GeneratedMedia")
        os.makedirs(folder_path, exist_ok=True)  # АВТОСОЗДАНИЕ ПАПКИ

        filename = f"art_{int(time.time())}.jpg"
        filepath = os.path.join(folder_path, filename)

        url = f"https://pollinations.ai{requests.utils.quote(prompt)}?width=1024&height=1024&seed=42&nofeed=true"
        img_data = requests.get(url, timeout=15).content

        with open(filepath, 'wb') as f:
            f.write(img_data)

        return f"Нейросетевой арт сохранен в: DemonShell/GeneratedMedia/{filename}"
    except Exception as e:
        return f"Ошибка генерации изображения: {str(e)}"
