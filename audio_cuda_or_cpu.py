# понимает форматы .ogg (телега) / .mp3
import whisper
import torch
import time
from datetime import datetime

audio_file = '1.ogg'

# Долгая проверка наличия GPU, включать только для проверки, назначать device вручную
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cuda"  # или "cpu"
current_time = datetime.now().strftime('%H:%M:%S')
print(f'{current_time}: Назначили девайс = {device}. Загружаем модель...')
model = whisper.load_model("large-v3").to(device)

# Расшифровка с ускорением GPU или без
start = time.time()
current_time = datetime.now().strftime('%H:%M:%S')
print(f'{current_time}: Начали расшифровку...')
result = model.transcribe(
    audio_file,
    language="ru",
    fp16=(device == "cuda")  # ускорение на GPU включится только для cuda
)
current_time = datetime.now().strftime('%H:%M:%S')
print(f'{current_time}: Закончили расшифровку\n')
end = time.time()

print(result["text"])

print(f"\nВремя расшифровки: {end - start:.2f} секунд")

# Длительность аудио из результатов Whisper
duration = result["segments"][-1]["end"]  # конец последнего сегмента
print(f"Длительность аудио: {duration:.2f} секунд")
