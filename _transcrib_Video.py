import whisper
import time
from datetime import datetime
import os
import subprocess
import tempfile

def get_log_time():
    return datetime.now().strftime('%H:%M:%S')

# Папка с видеофайлами
video_folder = "VIDEO"

# Поддерживаемые видеоформаты
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}

start = time.time()
device = "cuda"  # или "cpu"

log_file = "log.txt"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
text_result = f"text_result_{timestamp}.txt"

# Получаем список видеофайлов в папке
videos = [
    f for f in os.listdir(video_folder)
    if os.path.isfile(os.path.join(video_folder, f)) and
       any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)
]

with open(log_file, 'a', encoding='utf-8') as log:
    print(f"\nНайдено видеофайлов: {len(videos)}")
    log.write(f"Найдено видеофайлов: {len(videos)}\n")
    for video in videos:
        log.write(f"- {video}\n")

    print(f'{get_log_time()}: Назначили девайс = {device}. Загружаем модель...')
    log.write(f'{get_log_time()}: Назначили девайс = {device}. Загружаем модель...\n')
    model = whisper.load_model("large-v3").to(device)

    for file_number, video in enumerate(videos, start=1):
        video_path = os.path.join(video_folder, video)
        print(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...')
        log.write(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...\n')

        # Создаём временный аудиофайл
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            audio_path = tmp_audio.name

        try:
            # Извлекаем аудио из видео с помощью ffmpeg
            print(f'{get_log_time()}: Извлекаю аудио из {video}...')
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vn',  # отключаем видео
                '-acodec', 'pcm_s16le',  # кодек для WAV
                '-ar', '16000',  # частота дискретизации для Whisper
                '-ac', '1',  # моно
                '-y',  # перезаписывать без подтверждения
                audio_path
            ], capture_output=True, check=True)

            # Расшифровываем аудио
            print(f'{get_log_time()}: Расшифровываю аудио из {video}...')
            result = model.transcribe(
                audio_path,
                language="ru",
                fp16=(device == "cuda")
            )

            # Длительность аудио из результатов Whisper
            duration = result["segments"][-1]["end"]
            log.write(f'{get_log_time()}: Закончили расшифровку видео {video} (длительность {duration:.2f} сек)\n')
            log.write(f"Расшифровка: {result['text']}\n")

            # Записываем результат
            with open(text_result, 'a', encoding='utf-8') as f:
                f.write(f"*** Файл: {video} (длит. {duration:.2f} сек) ***\n")
                f.write(f"{result['text']}\n\n")

        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка при извлечении аудио из {video}: {e.stderr.decode()}"
            print(f'{get_log_time()}: {error_msg}')
            log.write(f'{get_log_time()}: {error_msg}\n')
        except Exception as e:
            error_msg = f"Ошибка при обработке {video}: {str(e)}"
            print(f'{get_log_time()}: {error_msg}')
            log.write(f'{get_log_time()}: {error_msg}\n')
        finally:
            # Удаляем временный аудиофайл
            if os.path.exists(audio_path):
                os.remove(audio_path)

    end = time.time()
    print(f"\nВремя всей обработки: {end - start:.2f} секунд")
    log.write(f"\nВремя всей обработки: {end - start:.2f} секунд\n")