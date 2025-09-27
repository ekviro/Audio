import ffmpeg


def cut_audio(audio_file, seg_len=17):
    duration = float(ffmpeg.probe(audio_file)['format']['duration'])
    pos, i = 0, 1

    while pos < duration:
        target = min(pos + seg_len, duration)

        # Ищем паузу в последних 5 секундах перед target
        try:
            out, _ = (ffmpeg.input(audio_file, ss=max(pos, target - 5), t=5)
                      .filter('silencedetect', n=-30, d=0.5)
                      .output('-', format='null')
                      .run(capture_stdout=True, capture_stderr=True))

            if 'silence_start:' in out.decode():
                pause_time = float(out.decode().split('silence_start: ')[1].split()[0])
                end = target - 5 + pause_time
            else:
                end = target
        except:
            end = target

        ffmpeg.input(audio_file, ss=pos, t=end - pos).output(f"part_{i:03d}.mp3").run(quiet=True)
        print(f"Part {i}: {end - pos:.1f}s")

        pos = end
        i += 1


cut_audio("audio.mp3")
