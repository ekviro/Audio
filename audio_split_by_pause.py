import ffmpeg


def cut_audio_sensitive(audio_file, seg_len=8):
    duration = float(ffmpeg.probe(audio_file)['format']['duration'])
    pos, i = 0, 1

    while pos < duration:
        target = pos + seg_len

        if target >= duration:
            end = duration
        else:
            # Очень чувствительные настройки для тихого аудио
            search_start = max(pos, target - 4)  # Увеличиваем окно поиска
            search_duration = min(8, duration - search_start)  # Больше времени для анализа

            try:
                # Более чувствительные параметры для тихого аудио
                process = (
                    ffmpeg
                    .input(audio_file, ss=search_start, t=search_duration)
                    .filter('silencedetect', n=-40, d=0.5)  # Очень низкий порог
                    .output('-', format='null')
                    .run_async(pipe_stderr=True, quiet=True)
                )

                _, stderr = process.communicate()
                output = stderr.decode()

                pauses = []
                for line in output.split('\n'):
                    if 'silence_start:' in line:
                        pause_rel = float(line.split('silence_start: ')[1].split()[0])
                        pause_abs = search_start + pause_rel
                        if pause_abs > pos + 2:  # Минимальная длительность сегмента
                            pauses.append(pause_abs)

                if pauses:
                    # Выбираем паузу ближайшую к target
                    end = min(pauses, key=lambda x: abs(x - target))
                    print(f"✓ Найдена пауза в {end:.1f}с")
                else:
                    end = target
                    print(f"× Паузы не найдены (тихое аудио), режем в {target:.1f}с")

            except Exception as e:
                end = target
                print(f"! Ошибка поиска, режем в {target:.1f}с")

        segment_duration = end - pos
        if segment_duration > 0.5:  # Минимальная длительность
            ffmpeg.input(audio_file, ss=pos, t=segment_duration).output(f"part_{i:03d}.mp3").run(quiet=True)
            print(f"Part {i}: {segment_duration:.1f}s (с {pos:.1f} по {end:.1f})")
            pos = end
            i += 1
        else:
            # Если сегмент слишком короткий, пропускаем вперед
            pos = target
            print("! Слишком короткий сегмент, пропускаем")


cut_audio_sensitive("audio.mp3")