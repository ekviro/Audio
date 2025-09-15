# понимает форматы .ogg (телега) / .mp3
import whisper
import time
from datetime import datetime
import re  # для работы с регулярными выражениями
import os

audio_file = 'audio_files/20150925194925.MP3'
target_word = 'новая заметка'

audio_folder = "audio_files"
all_text = []
audios = [
    f for f in os.listdir(audio_folder)
    if os.path.isfile(os.path.join(audio_folder, f))
]
print(f"В папке найдено файлов: {len(audios)}")
for audio in audios:
    print(f"- {audio}")

def regex_replace_any_case(text):
    """Разбиение текста на пункты по ключевому слову target_word."""
    counter = 1  # Счетчик для нумерации пунктов

    def replace_func(match):
        # Эта функция вызывается для каждого найденного совпадения
        nonlocal counter  # Используем внешнюю переменную counter
        result = f"\n{counter}. "  # Формируем замену: "1. ", "2. ", etc.
        counter += 1  # Увеличиваем счетчик для следующего найденного слова
        return result  # Возвращаем текст для замены

    # Создаем шаблон для поиска
    pattern = r'\b' + re.escape(target_word) + r'\b'  # Экранируем спецсимволы в слове (слово только целиком)
    # re.escape нужно, если в слове есть . * + ? и другие спецсимволы

    # Заменяем все вхождения
    return re.sub(
        pattern,  # Что ищем
        replace_func,  # На что заменяем (функция замены)
        text,  # Исходный текст
        flags=re.IGNORECASE  # Игнорируем регистр букв
    )

# Долгая проверка наличия GPU, включать только для проверки, назначать device вручную
# import torch
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cuda"  # или "cpu"
current_time = datetime.now().strftime('%H:%M:%S')
print(f'{current_time}: Назначили девайс = {device}. Загружаем модель...')
model = whisper.load_model("large-v3").to(device)

# Расшифровка с ускорением GPU или без
start = time.time()

for audio in audios:
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f'{current_time}: Начали расшифровку файла {audio}...')
    result = model.transcribe(
        os.path.join(audio_folder, audio),
        language="ru",
        fp16=(device == "cuda")  # ускорение на GPU включится только для cuda
    )
    current_time = datetime.now().strftime('%H:%M:%S')
    # Длительность аудио из результатов Whisper
    duration = result["segments"][-1]["end"]  # конец последнего сегмента
    print(f'{current_time}: Закончили расшифровку файла {audio} (длительностью {duration:.2f} секунд)')
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f'{current_time}: Начали разбиение на пункты по ключевому слову...')
    text = regex_replace_any_case(result["text"])
    all_text.append(text)
end = time.time()

print(f"\nВремя всей обработки: {end - start:.2f} секунд")
print("Результат:")
for res in all_text:
    print(res)






