import sounddevice as sd
import numpy as np
import webrtcvad
import whisper
import queue
import sys
import os
from datetime import datetime
import re
import soundfile as sf

# ========== НАСТРОЙКИ ==========
MODEL_NAME = "large-v3"
LANGUAGE = "ru"
PAUSE_SECONDS = 3.0
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 30
VAD_AGGRESSIVENESS = 3
OUTPUT_FOLDER = "."


# ================================

def create_output_file():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(OUTPUT_FOLDER, f"spicker-{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return filename


def split_into_sentences(text):
    text = re.sub(r'\b(т\.д|т\.п|т\.е|и\.т\.д|и\.т\.п|г\.|рис\.|табл\.)\b',
                  lambda m: m.group(0).replace('.', '␀'), text)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.replace('␀', '.').strip() for s in sentences]
    return [s for s in sentences if s]


def recognize_and_write(model, speech_buffer, output_file):
    if not speech_buffer:
        return

    audio_data = np.concatenate(speech_buffer, axis=0).flatten()
    duration = len(audio_data) / SAMPLE_RATE
    print(f"  Длина куска: {duration:.1f} сек")

    temp_wav = "temp_chunk.wav"
    sf.write(temp_wav, audio_data, SAMPLE_RATE)

    result = model.transcribe(temp_wav, language=LANGUAGE, fp16=False)
    raw_text = result["text"].strip()

    os.remove(temp_wav)

    if raw_text:
        sentences = split_into_sentences(raw_text)
        with open(output_file, "a", encoding="utf-8") as f:
            for s in sentences:
                f.write(s + "\n")
            f.write("\n")
        print(f"  Записано ({len(sentences)} предл.):")
        for s in sentences:
            print(f"    {s}")
    else:
        print("  (пусто)")


def main():
    output_file = create_output_file()
    print(f"Файл результатов: {output_file}")
    print(f"Загрузка Whisper {MODEL_NAME}...")
    model = whisper.load_model(MODEL_NAME)
    print("Whisper загружен.")

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    frame_size = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
    pause_frames = int(PAUSE_SECONDS * 1000 / FRAME_DURATION_MS)

    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        audio_queue.put(indata.copy())

    print("\nСлушаю... Говорите.")
    print(f"(пауза {PAUSE_SECONDS} сек = конец куска)\n")

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        dtype='int16', blocksize=frame_size, callback=audio_callback
    )

    with stream:
        while True:
            # Очищаем очередь перед началом нового куска
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    break

            speech_buffer = []
            silence_counter = 0
            is_speaking = False

            # Ждём и записываем кусок
            while True:
                try:
                    frame = audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                frame_bytes = frame.tobytes()
                try:
                    is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
                except Exception:
                    is_speech = False

                if is_speech:
                    speech_buffer.append(frame)
                    silence_counter = 0
                    is_speaking = True
                else:
                    if is_speaking:
                        silence_counter += 1
                        speech_buffer.append(frame)

                        if silence_counter >= pause_frames:
                            break  # Кусок закончен

            # Распознаём и пишем
            print("\n[Распознавание...]")
            recognize_and_write(model, speech_buffer, output_file)

            # Ждём Enter
            print("\n[Правь текст в файле. Нажми Enter, чтобы продолжить...]")
            input()

            # Очищаем очередь (то, что накопилось, пока правил)
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    break

            print("\nСлушаю... Говорите.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОстановлено пользователем.")