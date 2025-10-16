import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any
 telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import requests


class BotConfig:
from telegram import Update
from
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = json.load(f)

    @property
    def TELEGRAM_API_KEY(self) -> str:
        return self.config["TELEGRAM_API_KEY"]

    @property
    def GIGACHAT_API_URL(self) -> str:
        return self.config["GIGACHAT_API_URL"]

    @property
    def YANDEX_SPEECHKIT_API_KEY(self) -> str:
        return self.config["YANDEX_SPEECHKIT_API_KEY"]


def generate_response(prompt: str) -> str:
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "prompt": prompt,
        "max_tokens": 100,
        "temperature": 0.7,
    }
    response = requests.post(BOT_CONFIG.GIGACHAT_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get("choices")[0].get("text")
    else:
        raise Exception(
            f"GigaChat API request failed with status code {response.status_code}: {response.text}"
        )


def text_to_speech(text: str, output_file: str) -> None:
    cmd = [
        "curl",
        "-X",
        "POST",
        "-H",
        f"Authorization: Api-Key {BOT_CONFIG.YANDEX_SPEECHKIT_API_KEY}",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "--data-urlencode",
        f"text={text}",
        "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
        "-o",
        output_file,
    ]
    subprocess.run(cmd, check=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я ваш виртуальный помощник Корпоративного университета Московского метрополитена."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == "group":
        if "@your_bot_name" in text:
            new_text: str = text.replace("@your_bot_name", "").strip()
        else:
            return
    else:
        new_text = text

    try:
        giga_chat_response = generate_response(new_text)
        await update.message.reply_text(giga_chat_response)

        audio_file = Path("output.mp3")
        text_to_speech(giga_chat_response, audio_file)
        await update.message.reply_audio(audio=open(audio_file, "rb"))
        os.remove(audio_file)
    except Exception as e:
        print(e)
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса."
        )


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Упс! Произошла ошибка: {context.error}")


def main() -> None:
    global BOT_CONFIG
    BOT_CONFIG = BotConfig("config.json")

    app = Application.builder().token(BOT_CONFIG.TELEGRAM_API_KEY).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Run the bot
    print("Starting polling...")
    app.run_polling(poll_interval=3)


if name == "__main__":
    main()