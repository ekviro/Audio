# понимает форматы .ogg (телега) / .mp3
import whisper
import time
from datetime import datetime
import os

def get_log_time():
    return datetime.now().strftime('%H:%M:%S')

audio_folder = "RECORD"
start = time.time()
# Долгая проверка наличия GPU, включать только для проверки, назначать device вручную
# import torch
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"  # "cuda" или "cpu"

log_file = "log.txt"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
text_result = f"text_result_{timestamp}.txt"
audios = [
    f for f in os.listdir(audio_folder)
    if os.path.isfile(os.path.join(audio_folder, f))
]

with open(log_file, 'a') as log:
    print(f"\nВ папке найдено файлов: {len(audios)}")
    log.write(f"В папке найдено файлов: {len(audios)}\n")
    for audio in audios:
        log.write(f"- {audio}\n")

    print(f'{get_log_time()}: Назначили девайс = {device}. Загружаем модель...')
    log.write(f'{get_log_time()}: Назначили девайс = {device}. Загружаем модель...\n')
    model = whisper.load_model("large-v3").to(device)

    for n, audio in enumerate(audios, start=1):
        print(f'{get_log_time()}: Начали расшифровку файла {audio} ({n})...')
        log.write(f'{get_log_time()}: Начали расшифровку файла {audio} ({n})...\n')
        result = model.transcribe(
            os.path.join(audio_folder, audio),
            language="ru",
            fp16=(device == "cuda")  # ускорение на GPU включится только для cuda
        )
        # Длительность аудио из результатов Whisper
        duration = result["segments"][-1]["end"]  # конец последнего сегмента
        log.write(f'{get_log_time()}: Закончили расшифровку файла {audio} (длительностью {duration:.2f} секунд)\n')
        log.write(f"Расшифровка по файлу {audio}: {result['text']}\n")

        with open(text_result, 'a') as f:
            f.write(f"{n}. {result['text']}\n")
    end = time.time()

    print(f"\nВремя всей обработки: {end - start:.2f} секунд")
    log.write(f"\nВремя всей обработки: {end - start:.2f} секунд\n")
