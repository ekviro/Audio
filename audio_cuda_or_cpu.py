# понимает форматы .ogg (телега) / .mp3
import whisper
import torch
import time

audio_file = '1.ogg'

start = time.time()

# Проверяем и используем GPU если есть
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("large-v3").to(device)

# Расшифровка с ускорением GPU или без
result = model.transcribe(
    audio_file,
    language="ru",
    fp16=(device == "cuda")  # ускорение на GPU включится только для cuda
)

print(f"----- {device}")
print(result["text"])
end = time.time()
print(f"Время выполнения: {end - start:.2f} сек")
