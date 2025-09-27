import ffmpeg


def quick_split(audio_file, seconds=60):
    """Самый простой вариант"""
    duration = float(ffmpeg.probe(audio_file)['format']['duration'])

    for i in range(0, int(duration), seconds):
        ffmpeg.input(audio_file, ss=i, t=seconds).output(f'part_{i // seconds + 1}.mp3').run()


# Использование
quick_split("audio.MP3", 30)  # Нарезка на 30-секундные части