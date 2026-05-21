import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_MAX_MESSAGE = 4000


def truncate_message(message: str) -> str:
    if len(message) <= TELEGRAM_MAX_MESSAGE:
        return message

    return (
        message[: TELEGRAM_MAX_MESSAGE - 120]
        + "\n\n[AlphaScope] Message truncated due to Telegram size limits."
    )


def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing Telegram credentials")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": truncate_message(message),
    }

    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")

    return result


if __name__ == "__main__":
    result = send_telegram_message("AlphaScope test message: system online.")
    print(result)