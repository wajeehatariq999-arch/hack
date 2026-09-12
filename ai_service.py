"""
ai_service.py
------------------------------------------------------------
All communication with the Groq API goes through this file.
It uses the official Groq Python SDK (package name: "groq").

Function names/signatures are kept IDENTICAL to the previous
Gemini version (call_gemini_raw, get_client, run_feature, etc.)
so that app.py and safety.py do not need any changes.

Responsibilities:
  - Build/cache a Groq client from the API key in Streamlit secrets.
  - Provide a low-level `call_gemini_raw` used by safety.py for the
    relevance/emergency classification calls.
  - Provide a high-level `run_feature` that performs the full
    two-stage safety pipeline and then generates the final,
    feature-specific answer.
  - Turn every possible failure (missing key, invalid key, rate
    limit, timeout, network error, empty response, etc.) into a
    clear, friendly message instead of a crash.
------------------------------------------------------------
"""

from __future__ import annotations

import streamlit as st

from prompts import (
    FEATURE_PROMPTS,
    NOT_RELEVANT_MESSAGE,
    EMERGENCY_MESSAGE,
)
from safety import check_relevance, check_emergency

# NOTE: llama-3.1-8b-instant and llama-3.3-70b-versatile were
# decommissioned by Groq on 2026-08-16. Using their recommended
# replacements below. Other options:
#   "openai/gpt-oss-20b"  -> smaller/faster, replaces llama-3.1-8b-instant
#   "qwen/qwen3.6-27b"    -> alternative replacement for llama-3.3-70b-versatile
DEFAULT_MODEL = "openai/gpt-oss-120b"
REQUEST_TIMEOUT_SECONDS = 30


# ------------------------------------------------------------------
# Client setup
# ------------------------------------------------------------------
def get_api_key() -> str | None:
    """
    Reads the Groq API key from Streamlit secrets.
    Returns None if it is missing or still the placeholder value.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return None

    if not api_key or "ENTER_YOUR_GROQ_API_KEY_HERE" in api_key:
        return None

    return api_key


@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    """
    Creates (and caches) a Groq API client for the given key.
    Cached by Streamlit so we don't reconnect on every rerun.
    """
    from groq import Groq

    return Groq(api_key=api_key)


def _friendly_error_from_exception(exc: Exception) -> str:
    """
    Converts a raw SDK/network exception into a short, friendly,
    non-technical message for end users.
    """
    text = str(exc).lower()

    if "api key" in text or "api_key" in text or "unauthorized" in text or "permission" in text or "401" in text:
        return (
            "Your Groq API key seems to be missing or invalid. "
            "Please check the key in `.streamlit/secrets.toml` "
            "(or in Streamlit Cloud Secrets) and try again."
        )
    if "quota" in text or "rate limit" in text or "429" in text or "resource_exhausted" in text or "rate_limit_exceeded" in text:
        return (
            "SPG has hit the Groq API rate limit or quota for now. "
            "Please wait a short while and try again."
        )
    if "timeout" in text or "timed out" in text or "deadline" in text:
        return (
            "The request to the AI service timed out. Please check your "
            "internet connection and try again."
        )
    if "network" in text or "connection" in text or "dns" in text or "unreachable" in text:
        return (
            "SPG couldn't reach the Groq API. Please check your "
            "internet connection and try again."
        )
    if "safety" in text or "blocked" in text or "content_filter" in text or "recitation" in text:
        return (
            "The AI service was unable to generate a response for this "
            "specific input. Please rephrase your question and try again."
        )
    if "model" in text and ("not found" in text or "does not exist" in text or "decommissioned" in text):
        return (
            "The selected AI model is unavailable right now. Please try "
            "again shortly, or contact the app owner to update the model name."
        )

    return (
        "Something went wrong while contacting the AI service. "
        "Please try again in a moment. "
        f"(Technical detail: {str(exc)[:200]})"
    )


# ------------------------------------------------------------------
# Low-level call (used for classification prompts in safety.py)
# ------------------------------------------------------------------
def call_gemini_raw(client, model_name: str, prompt_text: str) -> tuple[str | None, str | None]:
    """
    Sends a single prompt to Groq and returns the raw text response.
    (Name kept as "call_gemini_raw" for compatibility with safety.py —
    it now talks to Groq under the hood.)

    Returns:
        (text, error_message)
        Exactly one of the two will be None.
    """
    if client is None:
        return None, "No AI client is configured (missing API key)."

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.0,
            max_tokens=20,
        )
        text = response.choices[0].message.content
        if not text:
            return None, "The AI service returned an empty response."
        return text, None

    except Exception as exc:  # noqa: BLE001 - we deliberately catch everything here
        return None, _friendly_error_from_exception(exc)


# ------------------------------------------------------------------
# High-level call (used by each feature page)
# ------------------------------------------------------------------
def generate_feature_answer(client, model_name: str, feature_key: str, user_prompt: str) -> tuple[str | None, str | None]:
    """
    Generates the final answer for a specific feature, using that
    feature's dedicated system instruction.

    Returns:
        (answer_text, error_message)
    """
    if feature_key not in FEATURE_PROMPTS:
        return None, "Unknown feature requested."

    system_instruction = FEATURE_PROMPTS[feature_key]
    final_contents = (
        "Respond now by directly following your system instructions. "
        "Do not greet the user or introduce yourself - start straight "
        "with the first required section heading.\n\n" + user_prompt
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": final_contents},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        text = response.choices[0].message.content
        if not text:
            return None, "The AI service returned an empty response. Please try again."
        return text, None

    except Exception as exc:  # noqa: BLE001
        return None, _friendly_error_from_exception(exc)


def run_feature(feature_key: str, user_prompt: str, raw_user_text: str) -> dict:
    """
    Runs the FULL pipeline for a feature:
      1. Validate API key / client
      2. Stage 1: relevance check
      3. Stage 2: emergency check
      4. Final generation

    `raw_user_text` is the plain combined text used for the safety
    classification stages. `user_prompt` is the fully formatted
    feature-specific prompt sent for the final answer.

    Returns a dict with keys:
        status: "ok" | "not_relevant" | "emergency" | "error"
        message: str (the text to display to the user)
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "status": "error",
            "message": (
                "⚠️ No valid Groq API key found. Please add your key to "
                "`.streamlit/secrets.toml` (locally) or to your app's "
                "Secrets (on Streamlit Cloud), then restart the app."
            ),
        }

    try:
        client = get_client(api_key)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": _friendly_error_from_exception(exc)}

    if not raw_user_text or not raw_user_text.strip():
        return {
            "status": "error",
            "message": "Please fill in the required fields before submitting.",
        }

    # Stage 2 first: an emergency should be caught even if the topic
    # is also correctly "relevant" - we still want emergency priority.
    is_emergency, emergency_err = check_emergency(client, DEFAULT_MODEL, raw_user_text)
    if is_emergency:
        return {"status": "emergency", "message": EMERGENCY_MESSAGE}

    # Stage 1: relevance check
    is_relevant, relevance_err = check_relevance(client, DEFAULT_MODEL, raw_user_text)
    if not is_relevant:
        return {"status": "not_relevant", "message": NOT_RELEVANT_MESSAGE}

    # Final generation
    answer, gen_err = generate_feature_answer(client, DEFAULT_MODEL, feature_key, user_prompt)
    if gen_err:
        return {"status": "error", "message": f"⚠️ {gen_err}"}

    return {"status": "ok", "message": answer}