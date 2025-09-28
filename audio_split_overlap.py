import ffmpeg


def cut_audio_with_overlap_fixed(audio_file, seg_len=8, overlap=2):
    duration = float(ffmpeg.probe(audio_file)['format']['duration'])
    pos, i = 0, 1

    print(f"Общая длительность: {duration:.1f}с")

    while pos < duration:
        # Определяем конец текущего сегмента
        end = min(pos + seg_len, duration)
        segment_duration = end - pos

        # Создаем сегмент только если он не слишком короткий
        if segment_duration > 0.5:  # Минимальная длительность
            ffmpeg.input(audio_file, ss=pos, t=segment_duration).output(f"part_{i:03d}.mp3").run(quiet=True)
            print(f"Part {i}: {pos:.1f}-{end:.1f}с ({segment_duration:.1f}с)")
            i += 1

        # Перемещаем позицию с учетом наложения
        pos += (seg_len - overlap)

        # Если следующий сегмент будет слишком коротким - выходим
        if pos + (seg_len - overlap) >= duration:
            # Создаем последний сегмент из оставшегося аудио
            if pos < duration:
                last_duration = duration - pos
                if last_duration > 0.5:
                    ffmpeg.input(audio_file, ss=pos, t=last_duration).output(f"part_{i:03d}.mp3").run(quiet=True)
                    print(f"Part {i}: {pos:.1f}-{duration:.1f}с ({last_duration:.1f}с) - последний")
            break


# Запуск
cut_audio_with_overlap_fixed("audio.mp3", 8, 2)
