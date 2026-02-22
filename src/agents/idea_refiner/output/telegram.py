import asyncio
import logging
import os
import re

from telegram import Bot
from telegram.constants import ParseMode

from agents.idea_refiner.generation.models import LABELS, MODELS

log = logging.getLogger(__name__)

TELEGRAM_MSG_LIMIT = 4096


def _md_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    return text


def _build_messages(theme: str | None, state: dict, total_elapsed: float, today: str) -> list[str]:
    winner_label = state.get("winner_label")
    winner_name = "N/A"
    if winner_label in LABELS:
        winner_name = MODELS[LABELS.index(winner_label)]["name"]

    header = (
        f"<b>Daily Idea Run — {today}</b>\n"
        f"Theme: {theme or 'Open (no theme)'}\n"
        f"Winner: <b>{winner_name}</b>\n"
        f"Elapsed: {total_elapsed:.1f}s\n"
    )

    scoreboard = "\n<b>Judge's Scoreboard</b>\n"
    for ev in sorted(
        state.get("all_evals", []),
        key=lambda e: e["acquisition_score"] + e["demand_score"] + e.get("build_score", 0),
        reverse=True,
    ):
        label = ev["idea_label"]
        name = MODELS[LABELS.index(label)]["name"] if label in LABELS else label
        acq, dem, bld = ev["acquisition_score"], ev["demand_score"], ev.get("build_score", 0)
        trophy = " 🏆" if label == winner_label else ""
        scoreboard += f"  {name}{trophy}: {acq}+{dem}+{bld} = <b>{acq + dem + bld}/30</b>\n"

    winner_ev = next(
        (e for e in state.get("all_evals", []) if e["idea_label"] == winner_label), None
    )
    judge_note = ""
    if winner_ev:
        judge_note = f"\n<b>Judge on the winner:</b>\n<i>{winner_ev['explanation']}</i>\n"

    summary = header + scoreboard + judge_note

    winning_idea_raw = state.get("winning_idea") or ""
    idea_section = f"\n<b>🏆 Winning Idea — {winner_name}</b>\n\n{_md_to_html(winning_idea_raw)}"

    full = summary + idea_section
    if len(full) <= TELEGRAM_MSG_LIMIT:
        return [full]

    msgs = [summary]
    for i in range(0, len(idea_section), TELEGRAM_MSG_LIMIT):
        msgs.append(idea_section[i : i + TELEGRAM_MSG_LIMIT])
    return msgs


def send_telegram_summary(theme: str | None, state: dict, total_elapsed: float, today: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    messages = _build_messages(theme, state, total_elapsed, today)

    async def _send() -> None:
        bot = Bot(token=token)
        for msg in messages:
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )

    try:
        asyncio.run(_send())
        log.info("   📬 Telegram notification sent (%d message(s))", len(messages))
    except Exception as exc:
        log.warning("   ⚠️ Telegram notification failed: %s", exc)
