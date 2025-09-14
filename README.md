# В систему установить конвертор аудио
скачать на сайте `ffmpeg-release-full.7z`
```
https://www.gyan.dev/ffmpeg/builds/
```

1. Скачайте этот ZIP-архив
2. Распакуйте например в C:\ffmpeg
3. Добавьте в PATH: C:\ffmpeg\bin
Например:
```
setx PATH "%PATH%;C:\ffmpeg\bin"
```
4. Перезапустить терминал (cmd) и PyCharm и проверить установку в терминале
```
ffmpeg -version

```

# Это будет в зависимостях
### Основная библиотека Whisper от OpenAI
```
pip install openai-whisper
```

### Для работы с аудиофайлами в питоне (если будет надо)
```
pip install ffmpeg-python
```

# Это вручную обновить
### Обновить Whisper
```
pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git
```


### без VPN
Скачать модель вручную там, где есть vpn
базовая 140 Мб
```
https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt
```
малая (побольше) 460 Мб
```
https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt
```
самая большая (лучшая для RU) 3 Гб
```
https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt
```

Положить ее в папку
C:\Users\ВашеИмя\.cache\whisper\

или куда угодно, но в коде указать путь:
model_path = r"C:\Users\ВашеИмя\.cache\whisper\base.pt"
model = whisper.load_model(model_path)

Названия моделей в коде (если уже загружена, то не будет загружать, а будет искать в стандартной папке)
model = whisper.load_model("base")
model = whisper.load_model("small")
model = whisper.load_model("large")