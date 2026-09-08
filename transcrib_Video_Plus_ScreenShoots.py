import whisper
import time
from datetime import datetime
import os
import subprocess
import tempfile


def get_log_time():
    return datetime.now().strftime('%H:%M:%S')


# --- НАСТРОЙКИ ---
video_folder = "RECORD"
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
        md_filename = f"{video_name}.md"

        print(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...')
        log.write(f'{get_log_time()}: Начали обработку видео {video} ({file_number}/{len(videos)})...\n')

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
                fp16=(device == "cuda")
            )
            duration = result["segments"][-1]["end"]
            log.write(f'{get_log_time()}: Закончили расшифровку видео {video} (длительность {duration:.2f} сек)\n')

            # --- 3. СНЯТИЕ СКРИНШОТОВ ПО СЦЕНАМ ---
            print(f'{get_log_time()}: Анализирую сцены для {video}...')
            screenshots_dir = os.path.join(video_folder, f"screenshots_{video_name}")
            os.makedirs(screenshots_dir, exist_ok=True)

            scene_pattern = os.path.join(screenshots_dir, f"{video_name}_scene_%04d.jpg")
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vf', 'select=gt(scene\\,0.3),setpts=N/FRAME_RATE/TB',
                '-vsync', 'vfr',
                '-frames:v', '99999',
                '-y', scene_pattern
            ], capture_output=True, check=True)

            screenshot_files = sorted([f for f in os.listdir(screenshots_dir) if f.endswith('.jpg')])
            screenshot_count = len(screenshot_files)
            log.write(f'{get_log_time()}: Найдено {screenshot_count} сцен для {video}\n')
            print(f'{get_log_time()}: Найдено {screenshot_count} сцен для {video}')

            # --- 4. СОЗДАНИЕ MD-ФАЙЛА ---
            print(f'{get_log_time()}: Создаю MD-файл {md_filename}...')

            with open(md_filename, 'w', encoding='utf-8') as md_file:
                md_file.write(f"# Расшифровка видео: {video}\n\n")
                md_file.write(f"**Длительность:** {duration:.2f} секунд\n\n")
                md_file.write(f"**Количество сцен (скриншотов):** {screenshot_count}\n\n")
                md_file.write("---\n\n")

                # Сопоставляем скриншоты с сегментами
                # Для каждого сегмента ищем ближайший скриншот
                screenshot_times = []
                for sf in screenshot_files:
                    # Извлекаем номер сцены из имени файла
                    num = int(sf.split('_')[-1].split('.')[0])
                    # Приблизительное время: каждый кадр сцены соответствует моменту в видео
                    # ffmpeg выдаёт кадры в момент смены сцены, но точное время не сохраняется
                    # Поэтому используем приближение: считаем, что сцены распределены равномерно
                    # Более точный способ требует парсинга вывода ffmpeg, но для простоты оставим так
                    screenshot_times.append((num, sf))

                # Если скриншотов нет, просто пишем текст
                if screenshot_count == 0:
                    md_file.write(f"## Полный текст расшифровки\n\n")
                    md_file.write(f"{result['text']}\n")
                else:
                    # Проходим по сегментам
                    for i, segment in enumerate(result['segments']):
                        start_time = segment['start']
                        text = segment['text'].strip()

                        start_min = int(start_time // 60)
                        start_sec = int(start_time % 60)
                        time_str = f"{start_min:02d}:{start_sec:02d}"

                        # Ищем скриншот, номер которого соответствует текущему сегменту
                        # Просто берём скриншот с номером, пропорциональным позиции сегмента
                        seg_index = i / len(result['segments'])
                        screenshot_idx = int(seg_index * screenshot_count)
                        if screenshot_idx >= screenshot_count:
                            screenshot_idx = screenshot_count - 1

                        if screenshot_count > 0 and screenshot_idx < len(screenshot_files):
                            screenshot_file = screenshot_files[screenshot_idx]
                            screenshot_path = os.path.join(screenshots_dir, screenshot_file)
                            rel_path = os.path.relpath(screenshot_path, os.path.dirname(md_filename))

                            md_file.write(f"## [{time_str}] {text}\n\n")
                            md_file.write(f"![Кадр из сцены]({rel_path})\n\n")
                        else:
                            md_file.write(f"## [{time_str}] {text}\n\n")

                        md_file.write("---\n\n")

                    # Полный текст в конце
                    md_file.write(f"## Полный текст расшифровки\n\n")
                    md_file.write(f"{result['text']}\n")

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