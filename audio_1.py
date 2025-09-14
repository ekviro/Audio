import whisper
# понимает форматы .ogg (телега) / .mp3

audio_files = [
    '1.ogg'
    ]

base_model = whisper.load_model("base")
small_model = whisper.load_model("small")
large_model = whisper.load_model("large")

for audio in audio_files:
    print('- - - - -')
    print('\nbase_model:')
    base_result = base_model.transcribe(audio)
    print(base_result['text'])

    print('\nsmall_model:')
    small_result = small_model.transcribe(audio)
    print(small_result['text'])

    print('\nlarge_model:')
    large_result = large_model.transcribe(audio)
    print(large_result['text'])




