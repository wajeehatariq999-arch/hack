"""
safety.py
------------------------------------------------------------
Implements the two-stage protection flow required before SPG
ever generates a final medical/pharmacy answer:

  Stage 1: Relevance check   -> is this about medicine/pharmacy/health?
  Stage 2: Emergency check   -> does this describe a possible emergency?

Both checks primarily use Gemini itself (via ai_service), with a
fast local keyword net used ONLY as a safety-net fallback for the
emergency check in case the AI call itself fails (e.g. no internet,
invalid key, rate limit). The keyword net can only ever make the app
MORE cautious (show the emergency banner), never less cautious.
------------------------------------------------------------
"""

from __future__ import annotations

from prompts import (
    RELEVANCE_CHECK_PROMPT,
    EMERGENCY_CHECK_PROMPT,
    EMERGENCY_KEYWORDS,
)


def local_emergency_keyword_hit(user_text: str) -> bool:
    """
    Fast, local, non-AI keyword scan used as a safety-net backup.
    Returns True if any known emergency keyword/phrase is present.
    This NEVER produces medical answers by itself - it only decides
    whether to show the emergency banner as an extra safety layer.
    """
    if not user_text:
        return False
    text = user_text.lower()
    return any(keyword in text for keyword in EMERGENCY_KEYWORDS)


def check_relevance(client, model_name: str, user_text: str) -> tuple[bool, str | None]:
    """
    Stage 1: Ask Gemini whether the user's input is related to
    medicine / pharmacy / healthcare.

    Returns:
        (is_relevant: bool, error_message: str | None)

    If the classification call itself fails (network/API issue), we
    fail OPEN for relevance (treat as relevant) so a real user isn't
    blocked by an infrastructure hiccup - the main safety priority is
    the emergency check, not the relevance check. The error message
    (if any) is returned so the caller can optionally surface it.
    """
    from ai_service import call_gemini_raw  # local import avoids circular import

    prompt = RELEVANCE_CHECK_PROMPT.format(user_input=user_text)
    result, error = call_gemini_raw(client, model_name, prompt)

    if error is not None:
        # Fail open on relevance - don't block the user just because
        # the classifier call failed. The generation step later will
        # still have its own error handling.
        return True, error

    normalized = (result or "").strip().upper()
    is_relevant = "NOT_RELEVANT" not in normalized
    return is_relevant, None


def check_emergency(client, model_name: str, user_text: str) -> tuple[bool, str | None]:
    """
    Stage 2: Ask Gemini whether the user's input describes a possible
    medical emergency, combined with a local keyword safety net.

    Returns:
        (is_emergency: bool, error_message: str | None)

    Here we fail SAFE: if the AI call fails, we fall back to the local
    keyword scan so a genuine emergency phrase is still caught even if
    Gemini is unreachable.
    """
    from ai_service import call_gemini_raw  # local import avoids circular import

    keyword_hit = local_emergency_keyword_hit(user_text)

    prompt = EMERGENCY_CHECK_PROMPT.format(user_input=user_text)
    result, error = call_gemini_raw(client, model_name, prompt)

    if error is not None:
        # AI check failed -> rely on the local keyword net only.
        return keyword_hit, error

    normalized = (result or "").strip().upper()
    ai_flagged = "NOT_EMERGENCY" not in normalized and "EMERGENCY" in normalized

    # Combine: if EITHER the AI or the keyword net flags it, treat as
    # an emergency. This is intentionally cautious.
    return (ai_flagged or keyword_hit), None
