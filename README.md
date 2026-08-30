# 🎬 Telegram Media Downloader Bot

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-red)
![ffmpeg](https://img.shields.io/badge/ffmpeg-media%20processing-007808?logo=ffmpeg&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Telegram-бот для скачивания видео из **YouTube, TikTok и Instagram** по ссылке
и его дальнейшей обработки: конвертация в MP3, обрезка по времени,
переименование с проставлением тегов артиста/названия.

## ✨ Возможности

- 📥 **Скачивание** видео по ссылке (YouTube / TikTok / Instagram) через `yt-dlp`
- 🎵 **Видео → MP3** конвертация через `ffmpeg`
- ✂️ **Обрезка** видео/аудио по диапазону времени (`00:10-00:40`)
- ✏️ **Переименование**: ставит ID3/метатеги артиста и названия и переименовывает файл
- 🔗 **Цепочки действий** — результат одного шага можно сразу передать в следующий
  (скачал → обрезал → в MP3 → переименовал)
- 📊 Живой прогресс скачивания прямо в чате
- 🧹 Автоматическая очистка временных файлов (при новой ссылке и по расписанию)

## 🧱 Технологический стек

| Компонент | Назначение |
|---|---|
| [Python 3.12](https://www.python.org/) | язык реализации |
| [aiogram 3](https://docs.aiogram.dev/) | асинхронный Telegram Bot API фреймворк, FSM для диалогов |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | скачивание видео с YouTube/TikTok/Instagram |
| [ffmpeg](https://ffmpeg.org/) | конвертация в MP3, обрезка, теги метаданных |
| `asyncio` | неблокирующая обработка + фоновая очистка файлов |
| Docker | контейнеризация для деплоя |

## 🗂 Структура проекта

```
├── bot.py            # хендлеры Telegram, FSM-диалоги, прогресс, очистка
├── downloader.py      # обёртка над yt-dlp: скачивание, очистка сессий
├── mediatools.py       # обёртка над ffmpeg: mp3, обрезка, теги
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 🚀 Запуск

### Локально

```bash
git clone https://github.com/NAPRINAR/telegram-bot-downloads.git
cd telegram-bot-downloads
pip install -r requirements.txt
```

Убедись, что `ffmpeg` доступен в PATH:

```bash
ffmpeg -version
```

Получи токен бота у [@BotFather](https://t.me/BotFather), скопируй `.env.example` в `.env`
и впиши токен:

```bash
cp .env.example .env
```

```
BOT_TOKEN=123456:ABC-твой-токен
```

Запусти бота:

```bash
python bot.py
```

### Через Docker

```bash
docker build -t telegram-bot-downloads .
docker run -d --env-file .env --name media-bot telegram-bot-downloads
```

## 💬 Как пользоваться

1. Пришли боту ссылку на видео (YouTube / TikTok / Instagram).
2. Под скачанным видео появятся кнопки:
   - **🎵 В MP3** — конвертирует последний файл в аудио.
   - **✂️ Обрезать** — попросит диапазон времени вида `00:10-00:40`.
   - **✏️ Переименовать** — попросит `Артист - Название`, проставит теги и переименует файл.
3. Действия комбинируются друг за другом. Новая ссылка начинает новую цепочку
   и стирает предыдущий рабочий файл.

## ⚠️ Ограничения

- Telegram не позволяет боту отправлять файлы больше **50 МБ** — видео по умолчанию
  скачивается не выше 720p, чтобы обычно укладываться в лимит.
- Бот работает на long polling, поэтому должен быть постоянно запущен
  (локально, на VM или в контейнере).

## ☁️ Деплой

Бот — обычный long-polling процесс, поэтому подходит любой хостинг, где можно
держать процесс включённым 24/7 и установить ffmpeg:

- **Локально / свой сервер** — `python bot.py` или Docker-контейнер как systemd-сервис.
- **Oracle Cloud Free Tier** — бесплатная VM навсегда, полный контроль над
  зависимостями.

Бесплатные тиры Railway/Render/Fly.io для постоянно работающих ботов сильно
урезаны и не гарантируют бесплатный 24/7 аптайм.

## 📄 Лицензия

[MIT](LICENSE)
