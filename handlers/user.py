from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import config
from database import db
from utils.matcher import find_best_match

router = Router(name="user")

WELCOME = (
    "👋 Welcome to Med Star Internal Medicine Clinic's assistant!\n\n"
    "Just type your question in plain language and I'll try to answer it. "
    "If I don't know the answer, I'll pass it along to our team.\n\n"
    "Commands:\n"
    "/faq — browse all questions I can answer\n"
    "/location — find us on the map\n"
    "/channel — join our Telegram channel\n"
    "/help — show this message again"
)


def contact_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Our location", url=config.maps_link)],
            [InlineKeyboardButton(text="📢 Our channel", url=config.channel_link)],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.touch_user(message.from_user.id, message.from_user.username)
    await message.answer(WELCOME, reply_markup=contact_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(WELCOME, reply_markup=contact_keyboard())


@router.message(Command("location"))
async def cmd_location(message: Message):
    await message.answer(
        "📍 Here's where you can find us:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Open in Google Maps", url=config.maps_link)]]
        ),
    )


@router.message(Command("channel"))
async def cmd_channel(message: Message):
    await message.answer(
        "📢 Join our Telegram channel for updates:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Open channel", url=config.channel_link)]]
        ),
    )


@router.message(Command("faq"))
async def cmd_list_faq(message: Message):
    faqs = await db.list_faqs()
    if not faqs:
        await message.answer("There are no FAQs set up yet — check back soon!")
        return

    by_category: dict[str, list] = {}
    for f in faqs:
        by_category.setdefault(f.category, []).append(f)

    lines = ["📋 <b>Frequently Asked Questions</b>\n"]
    for category, items in by_category.items():
        lines.append(f"\n<b>{category.title()}</b>")
        for f in items:
            lines.append(f"• {f.question}")
    lines.append("\nJust type a question and I'll match it to an answer.")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text)
async def handle_question(message: Message, bot: Bot):
    await db.touch_user(message.from_user.id, message.from_user.username)

    faqs = await db.list_faqs()
    match, score = find_best_match(message.text, faqs, config.match_threshold)

    if match:
        await db.increment_hits(match.id)
        await message.answer(match.answer)
        return

    # No confident match — log it and optionally forward to admins
    await db.log_unanswered(message.from_user.id, message.from_user.username, message.text)
    await message.answer(
        "I don't have a confident answer for that yet 🤔 I've logged your question "
        "so the team can follow up — feel free to try rephrasing it too."
    )

    if config.forward_unanswered and config.admin_ids:
        who = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"❓ Unanswered question from {who} (id {message.from_user.id}):\n\n{message.text}",
                )
            except Exception:
                pass
