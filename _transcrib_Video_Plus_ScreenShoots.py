import whisper
import time
from datetime import datetime
import os
import subprocess
import tempfile

# Делает скрины с интервалом и распознанный текст вставляет перед ним в .md

def get_log_time():
    return datetime.now().strftime('%H:%M:%S')


# --- НАСТРОЙКИ ---
video_folder = "VIDEO"  # папка с видеофайлами
INTERVAL = 5  # секунд между скриншотами
# -----------------

VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}

start = time.time()
device = "cuda"

log_file = "log.txt"

videos = [
    f for f in os.listdir(video_folder)
    if os.path.isfile(os.path.join(video_folder, f)) and
       any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)
]


def format_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


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
        video_name = os.path.splitext(video)[0]

        # --- СОЗДАЁМ ПАПКУ ДЛЯ ЭТОГО ВИДЕО ---
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_folder = f"video_result_{timestamp}_{video_name}"
        os.makedirs(result_folder, exist_ok=True)

        # Папка для скриншотов внутри result_folder
        screenshots_dir = os.path.join(result_folder, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        # MD-файл внутри result_folder
        md_filename = os.path.join(result_folder, f"{video_name}.md")

        print(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...')
        log.write(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...\n')
        log.write(f'{get_log_time()}: Результат в папке {result_folder}\n')

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            audio_path = tmp_audio.name

        try:
            # --- 1. ИЗВЛЕЧЕНИЕ АУДИО ---
            print(f'{get_log_time()}: Извлекаю аудио из {video}...')
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', audio_path
            ], capture_output=True, check=True)

            # --- 2. РАСШИФРОВКА АУДИО ---
            print(f'{get_log_time()}: Расшифровываю аудио из {video}...')
            result = model.transcribe(
                audio_path,
                language="ru",
                fp16=(device == "cuda"),
                word_timestamps=True
            )
            duration = result["segments"][-1]["end"]
            log.write(f'{get_log_time()}: Закончили расшифровку видео {video} (длительность {duration:.2f} сек)\n')

            # Собираем все слова с таймкодами
            all_words = []
            for segment in result['segments']:
                for word_info in segment.get('words', []):
                    all_words.append({
                        'word': word_info['word'].strip(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
            log.write(f'{get_log_time()}: Найдено {len(all_words)} слов\n')

            # --- 3. ГЕНЕРАЦИЯ ГРАНИЦ ПО ИНТЕРВАЛУ ---
            print(f'{get_log_time()}: Генерирую интервалы по {INTERVAL} сек...')

            boundaries = []
            current = 0.0
            while current < duration:
                boundaries.append(current)
                current += INTERVAL
            boundaries.append(duration)

            print(f'{get_log_time()}: Получено {len(boundaries) - 1} интервалов')

            # --- 4. ИЗВЛЕЧЕНИЕ СКРИНШОТОВ ---
            print(f'{get_log_time()}: Извлекаю скриншоты...')

            screenshot_info = []
            for i in range(len(boundaries) - 1):
                interval_start = boundaries[i]
                interval_end = boundaries[i + 1]

                # Берём кадр в конце интервала
                capture_time = min(interval_end, duration - 0.01)

                screenshot_filename = f"frame_{i + 1:04d}.jpg"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)

                subprocess.run([
                    'ffmpeg', '-ss', str(capture_time),
                    '-i', video_path,
                    '-frames:v', '1',
                    '-y', screenshot_path
                ], capture_output=True, check=True)

                words_in_interval = [
                    w for w in all_words
                    if interval_start <= w['start'] < interval_end
                ]
                interval_text = ' '.join([w['word'] for w in words_in_interval])

                # Относительный путь от MD-файла к скриншоту
                rel_path = os.path.relpath(screenshot_path, os.path.dirname(md_filename))

                screenshot_info.append({
                    'text': interval_text,
                    'rel_path': rel_path
                })

            print(f'{get_log_time()}: Извлечено {len(screenshot_info)} скриншотов')

            # --- 5. СОЗДАНИЕ MD-ФАЙЛА (ТОЛЬКО ТЕКСТ + КАРТИНКИ) ---
            print(f'{get_log_time()}: Создаю MD-файл {md_filename}...')

            with open(md_filename, 'w', encoding='utf-8') as md_file:
                # Только текст + картинки, без заголовков и времени
                for info in screenshot_info:
                    if info['text']:
                        md_file.write(f"{info['text']}\n\n")

                    md_file.write(f"![]({info['rel_path']})\n\n")

            print(f'{get_log_time()}: ✅ MD-файл создан: {md_filename}')
            log.write(f'{get_log_time()}: MD-файл создан: {md_filename}\n')

        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка при обработке {video}: {e.stderr.decode()}"
            print(f'{get_log_time()}: ❌ {error_msg}')
            log.write(f'{get_log_time()}: {error_msg}\n')
        except Exception as e:
            error_msg = f"Ошибка при обработке {video}: {str(e)}"
            print(f'{get_log_time()}: ❌ {error_msg}')
            log.write(f'{get_log_time()}: {error_msg}\n')
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    end = time.time()
    print(f"\n✅ Время всей обработки: {end - start:.2f} секунд")
    log.write(f"\n✅ Время всей обработки: {end - start:.2f} секунд\n")