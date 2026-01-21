# app/notifiers.py
from typing import List


def format_recommendations_message(titles: List[str]) -> str:
    if not titles:
        return "🎬 No hay recomendaciones disponibles en este momento."
    lines = ["🎬 Aquí tienes tus recomendaciones:", ""]
    for idx, t in enumerate(titles, 1):
        lines.append(f"{idx}. {t}")
    return "\n".join(lines)


def notify_telegram(
    message: str,
    enable: bool = False,
    token: str | None = None,
    chat_id: str | None = None,
) -> None:
    if not enable:
        return
    # Placeholder: in a real setup, send via Telegram API
    print("Telegram notification:\n" + message)
