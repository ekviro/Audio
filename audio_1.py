import whisper

audio_file = '1.mp3'
model = whisper.load_model("small")
result = model.transcribe(audio_file)

print(result['text'])
