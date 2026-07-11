from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from database import db

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


ADMIN_HELP = (
    "🔧 <b>Admin commands</b>\n\n"
    "<code>/addfaq question | answer | category | keyword1,keyword2</code>\n"
    "  (category and keywords are optional)\n"
    "<code>/editfaq id | new question | new answer</code>\n"
    "  (leave a field empty to keep it unchanged, e.g. <code>/editfaq 3 |  | new answer</code>)\n"
    "<code>/delfaq id</code>\n"
    "<code>/listfaq</code> — list all FAQs with their IDs\n"
    "<code>/unanswered</code> — show recent unanswered questions\n"
    "<code>/resolve id</code> — mark an unanswered entry as handled\n"
    "<code>/stats</code> — usage stats"
)


@router.message(Command("admin"))
async def cmd_admin_help(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(ADMIN_HELP, parse_mode="HTML")


@router.message(Command("addfaq"))
async def cmd_addfaq(message: Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.split(maxsplit=1)
    if len(raw) < 2:
        await message.answer("Usage:\n<code>/addfaq question | answer | category | keywords</code>", parse_mode="HTML")
        return

    parts = [p.strip() for p in raw[1].split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        await message.answer("You need at least a question and an answer, separated by |")
        return

    question, answer = parts[0], parts[1]
    category = parts[2] if len(parts) > 2 and parts[2] else "general"
    keywords = parts[3] if len(parts) > 3 else ""

    faq_id = await db.add_faq(question, answer, category, keywords)
    await message.answer(f"✅ Added FAQ #{faq_id}: \"{question}\"")


@router.message(Command("editfaq"))
async def cmd_editfaq(message: Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.split(maxsplit=1)
    if len(raw) < 2:
        await message.answer("Usage:\n<code>/editfaq id | new question | new answer</code>", parse_mode="HTML")
        return

    parts = [p.strip() for p in raw[1].split("|")]
    if not parts or not parts[0].isdigit():
        await message.answer("First field must be a numeric FAQ id.")
        return

    faq_id = int(parts[0])
    new_question = parts[1] if len(parts) > 1 and parts[1] else None
    new_answer = parts[2] if len(parts) > 2 and parts[2] else None

    if new_question is None and new_answer is None:
        await message.answer("Nothing to update — provide a new question and/or answer.")
        return

    ok = await db.edit_faq(faq_id, new_question, new_answer)
    await message.answer(f"✅ FAQ #{faq_id} updated." if ok else f"⚠️ No FAQ found with id {faq_id}.")


@router.message(Command("delfaq"))
async def cmd_delfaq(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Usage: <code>/delfaq id</code>", parse_mode="HTML")
        return

    faq_id = int(parts[1].strip())
    ok = await db.delete_faq(faq_id)
    await message.answer(f"🗑️ Deleted FAQ #{faq_id}." if ok else f"⚠️ No FAQ found with id {faq_id}.")


@router.message(Command("listfaq"))
async def cmd_listfaq(message: Message):
    if not is_admin(message.from_user.id):
        return

    faqs = await db.list_faqs()
    if not faqs:
        await message.answer("No FAQs yet. Add one with /addfaq")
        return

    lines = []
    for f in faqs:
        lines.append(f"#{f.id} [{f.category}] {f.question} → {f.answer[:50]}{'…' if len(f.answer) > 50 else ''} (hits: {f.hits})")
    await message.answer("\n".join(lines))


@router.message(Command("unanswered"))
async def cmd_unanswered(message: Message):
    if not is_admin(message.from_user.id):
        return

    rows = await db.list_unanswered()
    if not rows:
        await message.answer("No pending unanswered questions 🎉")
        return

    lines = ["🕵️ <b>Recent unanswered questions</b>\n"]
    for entry_id, user_id, username, question, created_at in rows:
        who = f"@{username}" if username else str(user_id)
        lines.append(f"#{entry_id} ({who}, {created_at[:16]}): {question}")
    lines.append("\nMark handled with /resolve id")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("resolve"))
async def cmd_resolve(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Usage: <code>/resolve id</code>", parse_mode="HTML")
        return

    entry_id = int(parts[1].strip())
    ok = await db.resolve_unanswered(entry_id)
    await message.answer(f"✅ Marked #{entry_id} as resolved." if ok else f"⚠️ No entry found with id {entry_id}.")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    s = await db.stats()
    lines = [
        "📊 <b>Bot stats</b>",
        f"FAQs: {s['faqs']}",
        f"Users seen: {s['users']}",
        f"Unresolved questions: {s['unresolved']}",
    ]
    if s["top"]:
        lines.append("\n<b>Top questions:</b>")
        for question, hits in s["top"]:
            lines.append(f"• {question} ({hits} hits)")
    await message.answer("\n".join(lines), parse_mode="HTML")
