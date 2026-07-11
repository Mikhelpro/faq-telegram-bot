"""
Finds the best-matching FAQ for an incoming user question.

Uses rapidfuzz to score the user's text against each FAQ's stored question
AND its keyword list, so a hit on either counts. This is intentionally
lightweight (no embeddings / no external API calls) so the bot has zero
extra cost or latency — good enough for a focused FAQ set. Swap in a
semantic/embedding matcher later if the FAQ list grows large or phrasing
varies a lot.
"""
from rapidfuzz import fuzz
from database import Faq


def find_best_match(user_text: str, faqs: list[Faq], threshold: int) -> tuple[Faq | None, int]:
    if not faqs:
        return None, 0

    user_text = user_text.strip().lower()
    best_faq, best_score = None, 0

    for faq in faqs:
        question_score = fuzz.token_set_ratio(user_text, faq.question.lower())

        keyword_score = 0
        if faq.keywords:
            for kw in faq.keywords.split(","):
                kw = kw.strip().lower()
                if not kw:
                    continue
                keyword_score = max(keyword_score, fuzz.partial_ratio(user_text, kw))

        score = max(question_score, keyword_score)
        if score > best_score:
            best_faq, best_score = faq, score

    if best_score >= threshold:
        return best_faq, best_score
    return None, best_score
