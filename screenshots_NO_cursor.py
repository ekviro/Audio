import ffmpeg
import cv2
import numpy as np
import os
from datetime import datetime

# Для скрипта нужно видео без курсора и с медленным движением (чтобы каждое изменение побыло на экране). Тогда хорошо фоткает, но могут быть лишние кадры.
# Можно пиксели даже 1 поставить

# ========== НАСТРОЙКИ ==========
PIXEL_THRESHOLD = 100  # если изменилось > 100 пикселей — сохраняем
INPUT_FOLDER = "VIDEO"
OUTPUT_FOLDER = "."


# ================================

def get_video_resolution(video_path):
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return int(video_stream['width']), int(video_stream['height'])


def get_video_fps(video_path):
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    num = int(video_stream['r_frame_rate'].split('/')[0])
    den = int(video_stream['r_frame_rate'].split('/')[1])
    return num / den


def save_frame_at_time(video_path, timestamp, output_path):
    ffmpeg.input(video_path, ss=timestamp).output(
        output_path,
        vframes=1,
        qscale=2
    ).run(overwrite_output=True, quiet=True)


def process_video(video_path, output_folder, pixel_threshold=PIXEL_THRESHOLD):
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_folder = os.path.join(output_folder, f"screenshots_{folder_name}")
    os.makedirs(result_folder, exist_ok=True)

    print(f"\nОбработка: {os.path.basename(video_path)}")
    print(f"Скриншоты сохраняются в: {result_folder}/")
    print(f"Порог пикселей: {pixel_threshold}")

    width, height = get_video_resolution(video_path)
    fps = get_video_fps(video_path)
    print(f"Размер видео: {width}x{height}")
    print(f"FPS: {fps:.1f}")

    # Читаем КАЖДЫЙ кадр в ОРИГИНАЛЬНОМ размере
    process = (
        ffmpeg
        .input(video_path)
        # .filter("scale", 640, -1)  ← УБРАЛИ!
        .output("pipe:", format="rawvideo", pix_fmt="gray")
        .run_async(pipe_stdout=True)
    )

    prev_gray = None
    timestamp = 0
    saved_count = 0
    frame_count = 0

    while True:
        small_size = width * height  # оригинальный размер
        raw = process.stdout.read(small_size)

        if not raw:
            break

        gray = np.frombuffer(raw, dtype=np.uint8).reshape(height, width)

        timestamp = frame_count / fps

        if prev_gray is None:
            filename = os.path.join(result_folder, f"{timestamp:.1f}".replace('.', '-') + ".jpg")
            save_frame_at_time(video_path, timestamp, filename)
            prev_gray = gray.copy()
            saved_count += 1
            print(f"[{saved_count}] {os.path.basename(filename)} (кадр {frame_count})")
        else:
            diff = cv2.absdiff(gray, prev_gray)
            non_zero = np.count_nonzero(diff)

            if non_zero > pixel_threshold:
                filename = os.path.join(result_folder, f"{timestamp:.1f}".replace('.', '-') + ".jpg")
                save_frame_at_time(video_path, timestamp, filename)
                prev_gray = gray.copy()
                saved_count += 1
                print(
                    f"[{saved_count}] {os.path.basename(filename)} (кадр {frame_count}, изменилось {non_zero} пикселей)")
            else:
                print(f"  Пропущен кадр {frame_count} ({timestamp:.1f}с), изменилось {non_zero} пикселей")

        frame_count += 1

    process.wait()
    print(f"Готово! Сохранено {saved_count} кадров из {frame_count}")
    return saved_count


def process_all_videos(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER):
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

    print(f"Найдено {len(video_files)} видеофайлов")

    total_saved = 0
    for i, video_path in enumerate(video_files, 1):
        print(f"\n{'=' * 50}")
        print(f"Видео {i}/{len(video_files)}")
        print(f"{'=' * 50}")
        saved = process_video(video_path, output_folder)
        total_saved += saved

    print(f"\nВСЕ ГОТОВО! Сохранено {total_saved} кадров")


if __name__ == "__main__":
    process_all_videos()