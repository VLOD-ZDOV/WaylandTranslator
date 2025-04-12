import subprocess
import base64
import requests
import json
import time
import os
from PIL import Image

def capture_fullscreen(temp_path):
    """
    Делает фуллскрин скриншот с помощью spectacle.
    """
    cmd = [
        "spectacle",
        "--background",
        "--fullscreen",
        "--output", temp_path,
        "--nonotify"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return os.path.exists(temp_path)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка Spectacle: {e.stderr}")
        return False

def crop_bottom_half(image_path, output_path):
    """
    Обрезает нижнюю половину изображения.
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        # Координаты нижней половины
        box = (0, height // 2, width, height)
        cropped = img.crop(box)
        cropped.save(output_path)
        return output_path
    except Exception as e:
        print(f"Ошибка при обрезке изображения: {e}")
        return None

def translate_image(image_path):
    """
    Отправляет изображение на перевод через Gemma.
    """
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "gemma3:4b",
            "prompt": "1. Извлеки текст с изображения. 2. Переведи его на русский язык. Верни только переведённый текст.",
            "images": [image_data],
            "stream": False
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return json.loads(response.text)["response"]
        return "Ошибка перевода"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def show_notification(text):
    """
    Показывает перевод через уведомление.
    """
    try:
        subprocess.run(["notify-send", "Перевод", text, "-t", "5000"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка уведомления: {e}")

# Настройки путей
TEMP_PATH = "temp_screenshot.png"
FINAL_PATH = "screenshot.png"

# Основной цикл
last_text = ""
while True:
    try:
        if capture_fullscreen(TEMP_PATH):
            cropped = crop_bottom_half(TEMP_PATH, FINAL_PATH)
            if cropped and os.path.exists(FINAL_PATH):
                result = translate_image(FINAL_PATH)
                if result != last_text and "Ошибка" not in result and result.strip():
                    print(f"Перевод: {result}")
                    show_notification(result)
                    last_text = result
                os.remove(FINAL_PATH)
            os.remove(TEMP_PATH)
        else:
            print("Скриншот не удалось сделать.")
        time.sleep(2)
    except Exception as e:
        print(f"Ошибка в цикле: {str(e)}")
        time.sleep(5)
