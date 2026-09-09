import ffmpeg
import os
from datetime import datetime

# ========== НАСТРОЙКИ ==========
INTERVAL = 3  # Кадр каждые N секунд
INPUT_FOLDER = "VIDEO"  # Папка с исходными видео
OUTPUT_FOLDER = "."  # Папка для результатов (корень проекта)


# ================================

def get_video_resolution(video_path):
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return int(video_stream['width']), int(video_stream['height'])


def get_video_duration(video_path):
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return float(video_stream['duration'])


def process_video(video_path, output_folder, interval=INTERVAL):
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_folder = os.path.join(output_folder, f"screenshots_{folder_name}")
    os.makedirs(result_folder, exist_ok=True)

    print(f"\nОбработка: {os.path.basename(video_path)}")
    print(f"Скриншоты сохраняются в: {result_folder}/")

    width, height = get_video_resolution(video_path)
    duration = get_video_duration(video_path)
    print(f"Размер видео: {width}x{height}")
    print(f"Длительность видео: {duration:.1f} секунд")

    timestamp = 0
    saved_count = 0

    while timestamp < duration:
        filename = os.path.join(result_folder, f"{timestamp:.1f}".replace('.', '-') + ".jpg")

        ffmpeg.input(video_path, ss=timestamp).output(
            filename,
            vframes=1,
            qscale=2
        ).run(overwrite_output=True, quiet=True)

        saved_count += 1
        print(f"[{saved_count}] {os.path.basename(filename)} (время: {timestamp:.1f}с)")

        timestamp += interval

    print(f"Готово! Сохранено {saved_count} кадров")
    return saved_count


def process_all_videos(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER, interval=INTERVAL):
    if not os.path.exists(input_folder):
        print(f"Папка {input_folder}/ не найдена!")
        return

    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
    video_files = []

    for file in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in video_extensions:
                video_files.append(file_path)

    if not video_files:
        print(f"Видеофайлы не найдены в папке {input_folder}/")
        return

    print(f"Найдено {len(video_files)} видеофайлов:")
    for vf in video_files:
        print(f"  - {os.path.basename(vf)}")

    total_saved = 0
    for i, video_path in enumerate(video_files, 1):
        print(f"\n{'=' * 50}")
        print(f"Видео {i}/{len(video_files)}")
        print(f"{'=' * 50}")
        saved = process_video(video_path, output_folder, interval)
        total_saved += saved

    print(f"\n{'=' * 50}")
    print(f"ВСЕ ГОТОВО! Обработано {len(video_files)} видео, сохранено {total_saved} кадров")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    process_all_videos()