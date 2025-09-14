import whisper

model = whisper.load_model("base")

audio_file = '1.mp3'
result = model.transcribe(audio_file)
print(result['text'])

print()
audio_file = '2.ogg'
result = model.transcribe(audio_file)
print(result['text'])
