# Плагин процедурной генерации музыки
import os
import time
import numpy as np
import scipy.io.wavfile as wav


def generate_free_music(prompt: str) -> str:
    """Синтезирует аудиоклипы и музыку по математическим алгоритмам. Автоматически разворачивает GeneratedMusic."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.join(base_dir, "DemonShell", "GeneratedMusic")
        os.makedirs(folder_path, exist_ok=True)  # АВТОСОЗДАНИЕ ПАПКИ

        filename = f"track_{int(time.time())}.wav"
        filepath = os.path.join(folder_path, filename)

        sample_rate = 44100
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        # Математический синтез аккорда
        wave = 0.5 * np.sin(2 * np.pi * 440.0 * t) + 0.3 * np.sin(2 * np.pi * 554.37 * t) + 0.2 * np.sin(
            2 * np.pi * 659.25 * t)
        audio_data = (wave * 32767).astype(np.int16)

        wav.write(filepath, sample_rate, audio_data)
        return f"Аудиоклип успешно сгенерирован в: DemonShell/GeneratedMusic/{filename}"
    except Exception as e:
        return f"Ошибка генерации звука: {str(e)}"
