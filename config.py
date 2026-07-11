import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> list[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_ids: list[int] = field(default_factory=lambda: _parse_admin_ids(os.getenv("ADMIN_IDS", "")))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "faq_bot.db"))
    match_threshold: int = field(default_factory=lambda: int(os.getenv("MATCH_THRESHOLD", "65")))
    # Optional: if set, unmatched questions get forwarded to admins for a manual reply
    forward_unanswered: bool = field(
        default_factory=lambda: os.getenv("FORWARD_UNANSWERED", "true").lower() == "true"
    )
    maps_link: str = field(
        default_factory=lambda: os.getenv("MAPS_LINK", "https://maps.app.goo.gl/ExwuLXpEFckRJnzXA")
    )
    channel_link: str = field(
        default_factory=lambda: os.getenv("CHANNEL_LINK", "https://t.me/medstarinternalclinic")
    )


config = Config()

if not config.bot_token:
    raise RuntimeError(
        "BOT_TOKEN is not set. Create a .env file (see .env.example) or set the "
        "environment variable before starting the bot."
    )

if not config.admin_ids:
    print("[WARN] No ADMIN_IDS configured — admin commands will be unusable until you set one.")
