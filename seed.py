"""
Seed data for Med Star Internal Medicine Clinic's FAQ bot. This file is
checked into the repo, so on Render's free plan (no persistent disk — SQLite
data is wiped on every restart/redeploy) these FAQs get re-inserted
automatically on every startup if the table is empty.

Edit SEED_FAQS below and redeploy to update the baseline FAQ set. Anything
added later via /addfaq in Telegram will NOT survive a restart on the free
plan — see README for details and options (upgrade to a paid plan with a
disk, or migrate to Render Postgres).

NOTE: one entry below is still marked [PLACEHOLDER] — insurance providers
accepted are not yet confirmed. Everything else (phone, services, hours,
location) is filled in.
"""
import asyncio
from database import db

SEED_FAQS = [
    (
        "What are your working hours?",
        "We're open full-time, every day of the week. Come by anytime for a consultation.",
        "general",
        "hours,open,available,when,time,schedule",
    ),
    (
        "Where is the clinic located?",
        "You can find us here: use /location to get directions on Google Maps.",
        "general",
        "location,address,where,directions,find you",
    ),
    (
        "How do I book an appointment?",
        "Call us at 0116354280 to book an appointment. Walk-ins are also welcome.",
        "appointments",
        "appointment,book,booking,schedule,reserve",
    ),
    (
        "What services do you offer?",
        "We offer full internal medicine check-ups. Let us know your specific concern and "
        "we'll guide you from there.",
        "services",
        "services,offer,treatment,checkup,consultation",
    ),
    (
        "Do you accept insurance?",
        "[PLACEHOLDER] Please contact us directly at 0116354280 to confirm which insurance "
        "providers we currently accept.",
        "billing",
        "insurance,payment,cover,covered",
    ),
    (
        "What is your phone number?",
        "You can reach us at 0116354280, or message us here on Telegram.",
        "general",
        "phone,number,call,contact",
    ),
]


async def seed_if_empty():
    existing = await db.list_faqs()
    if existing:
        return
    for question, answer, category, keywords in SEED_FAQS:
        await db.add_faq(question, answer, category, keywords)


async def main():
    await db.init()
    await seed_if_empty()
    faqs = await db.list_faqs()
    print(f"Seeded. FAQ count: {len(faqs)}")


if __name__ == "__main__":
    asyncio.run(main())

