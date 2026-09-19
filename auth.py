"""
auth.py
------------------------------------------------------------
SPG - Smart Pharma Guider
Sign Up / Sign In system (v3 - automatic light / dark theme).

- Users are stored in a local SQLite file (users.db).
- Passwords are never stored as plain text: each one is salted and
  hashed with PBKDF2-HMAC-SHA256.
- Uses only the Python standard library + Streamlit, so
  requirements.txt does not change.
- The login page AND the logged-in app follow the phone's / browser's
  light or dark mode automatically (prefers-color-scheme). All of it
  lives in this file, so app.py needs no changes.

Public functions (used by app.py):
    require_login()        -> shows the Sign in / Create account page
                              and stops the app until the user is in.
    render_sidebar_user()  -> user card + Log out button for the sidebar.
------------------------------------------------------------
"""

import hashlib
import hmac
import html
import re
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import streamlit as st

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "users.db"
PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128
MAX_NAME_LEN = 80
MAX_FAILED_ATTEMPTS = 5      # wrong passwords allowed in one session...
LOCKOUT_SECONDS = 60         # ...before sign-in pauses for this long
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------
# DATABASE + PASSWORD HELPERS
# ------------------------------------------------------------------
def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt          TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    ).hex()


def create_user(full_name: str, email: str, password: str) -> bool:
    """Returns False if an account with this email already exists."""
    salt = secrets.token_bytes(16)
    try:
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash, salt) "
                "VALUES (?, ?, ?, ?)",
                (full_name, email, _hash_password(password, salt), salt.hex()),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return False
    return True


def verify_user(email: str, password: str):
    """Returns {"name", "email"} when the credentials match, else None."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT full_name, email, password_hash, salt FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None:
        _hash_password(password, b"\x00" * 16)  # keeps response time similar
        return None

    name, mail, stored_hash, salt_hex = row
    candidate = _hash_password(password, bytes.fromhex(salt_hex))
    if hmac.compare_digest(candidate, stored_hash):
        return {"name": name, "email": mail}
    return None


# ------------------------------------------------------------------
# SESSION HELPERS
# ------------------------------------------------------------------
def _locked_seconds() -> int:
    until = st.session_state.get("auth_locked_until", 0)
    remaining = until - time.time()
    return int(remaining) + 1 if remaining > 0 else 0


def _register_failure():
    count = st.session_state.get("auth_failures", 0) + 1
    if count >= MAX_FAILED_ATTEMPTS:
        st.session_state["auth_locked_until"] = time.time() + LOCKOUT_SECONDS
        count = 0
    st.session_state["auth_failures"] = count


def _log_in(user: dict):
    st.session_state["user"] = user
    st.session_state["page"] = "home"
    st.session_state.pop("auth_failures", None)
    st.rerun()


def logout():
    st.session_state.pop("user", None)
    st.session_state["page"] = "home"
    st.rerun()


# ------------------------------------------------------------------
# THEME 1 - logged-in app (custom cards, headings, result boxes)
#
# app.py builds its colours from CSS variables (--spg-*), so in dark
# mode we only re-define those variables. The few colours that are
# hard-coded in app.py (borders, card headings, emergency text) get
# their own dark override below. Light mode is left completely
# untouched: everything here lives inside the dark media query.
#
# This is injected on EVERY run (login page and app), because
# Streamlit rebuilds the page on every rerun.
# ------------------------------------------------------------------
APP_THEME_CSS = """
<style>
@media (prefers-color-scheme: dark) {

    /* re-define app.py's colour variables */
    .stApp {
        --spg-bg: #0E1716;
        --spg-card: #15211F;
        --spg-text: #E3F1EE;
        --spg-muted: #9DB8B2;
        --spg-teal-light: #1B3A36;
        --spg-danger-bg: #3A1714;
    }

    /* home-page feature cards */
    .stApp .spg-card {
        border-color: #2A3F3B !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
    }
    .stApp .spg-card-wrap:hover .spg-card {
        box-shadow: 0 10px 24px rgba(0,0,0,0.5) !important;
    }
    .stApp .spg-card h3,
    .stApp .feature-header h2 {
        color: #BFEFE6 !important;
    }

    /* "Open ->" button under each card */
    .stApp .spg-card-wrap .stButton>button {
        border-color: #2A3F3B !important;
        border-top-color: #2A3F3B !important;
        color: #BFEFE6 !important;
    }
    .stApp .spg-card-wrap .stButton>button:hover {
        background: var(--spg-teal-mid) !important;
        color: #FFFFFF !important;
    }

    /* result box */
    .stApp .result-card {
        border-color: #2A3F3B !important;
        border-left-color: var(--spg-accent) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
    }

    /* emergency box: keep the red, make the text readable */
    .stApp .emergency-card,
    .stApp .emergency-card * {
        color: #F5B7B1 !important;
    }

    /* small details */
    .stApp .spg-disclaimer { border-top-color: #2A3F3B !important; }
    .stApp section[data-testid="stSidebar"] .spg-disclaimer {
        border-top-color: #D3E4E0 !important;   /* sidebar stays teal, as before */
    }
    .stApp .stTextInput>div>div>input,
    .stApp .stTextArea textarea,
    .stApp .stSelectbox>div>div {
        border-color: #2F4642 !important;
    }
}
</style>
"""


# ------------------------------------------------------------------
# THEME 2 - login / sign-up page
#
# Every colour is a variable (--a-*). Light values first, then the
# dark values inside the media query. To change a login colour later,
# change it in ONE place below.
# ------------------------------------------------------------------
AUTH_CSS = """
<style>
/* let the browser draw native bits (scrollbar, autofill, eye icon) in the right mode */
:root, .stApp { color-scheme: light dark; }

/* ================= LIGHT MODE COLOURS (default) ================= */
:root {
    --a-page:        #F3FAF8;
    --a-glow-1:      #D3F0E8;
    --a-glow-1-t:    rgba(211,240,232,0);
    --a-glow-2:      #C9E9E1;
    --a-glow-2-t:    rgba(201,233,225,0);
    --a-cap-1:       #A6DFD1;
    --a-cap-2:       #E4F3F0;

    --a-card:        #FFFFFF;
    --a-card-border: #E3ECEA;
    --a-card-shadow: 0 30px 60px -24px rgba(11,61,58,0.40), 0 8px 20px rgba(15,94,86,0.08);

    --a-title:       #0B3D3A;
    --a-sub:         #5C7A75;
    --a-label:       #16302C;

    --a-tab-bg:          #E4F3F0;
    --a-tab-text:        #5C7A75;
    --a-tab-active-bg:   #FFFFFF;
    --a-tab-active-text: #0F5E56;
    --a-tab-shadow:      0 2px 8px rgba(15,94,86,0.16);

    --a-input-bg:        #F7FAF9;
    --a-input-border:    #D3E4E0;
    --a-input-focus-bg:  #FFFFFF;
    --a-input-text:      #16302C;
    --a-placeholder:     #8FA9A4;
    --a-icon:            #5C7A75;
    --a-caret:           #0F5E56;

    --a-trust-bg:    #E4F3F0;
    --a-trust-text:  #0F5E56;
}

/* ================= DARK MODE COLOURS ================= */
@media (prefers-color-scheme: dark) {
    :root {
        --a-page:        #0A1211;
        --a-glow-1:      #103631;
        --a-glow-1-t:    rgba(16,54,49,0);
        --a-glow-2:      #0D2C28;
        --a-glow-2-t:    rgba(13,44,40,0);
        --a-cap-1:       #1F5A50;
        --a-cap-2:       #16302C;

        --a-card:        #121D1B;
        --a-card-border: #263D39;
        --a-card-shadow: 0 30px 60px -24px rgba(0,0,0,0.70), 0 8px 20px rgba(0,0,0,0.35);

        --a-title:       #E3F1EE;
        --a-sub:         #9DB8B2;
        --a-label:       #D5E8E4;

        --a-tab-bg:          #1B2B29;
        --a-tab-text:        #9DB8B2;
        --a-tab-active-bg:   #24413C;
        --a-tab-active-text: #BFEFE6;
        --a-tab-shadow:      0 2px 8px rgba(0,0,0,0.40);

        --a-input-bg:        #0E1716;
        --a-input-border:    #2F4642;
        --a-input-focus-bg:  #0B1413;
        --a-input-text:      #E3F1EE;
        --a-placeholder:     #6F8C86;
        --a-icon:            #9DB8B2;
        --a-caret:           #2FBFA1;

        --a-trust-bg:    #1B3A36;
        --a-trust-text:  #BFEFE6;
    }
}

/* ---------- hide sidebar on the login page ---------- */
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

/* ---------- page background: soft glow + two floating capsules ---------- */
.stApp {
    background:
        radial-gradient(900px 520px at 6% 0%, var(--a-glow-1) 0%, var(--a-glow-1-t) 65%),
        radial-gradient(820px 540px at 100% 100%, var(--a-glow-2) 0%, var(--a-glow-2-t) 65%),
        var(--a-page) !important;
}
.stApp::before, .stApp::after {
    content: ""; position: fixed; z-index: 0; pointer-events: none;
    border-radius: 999px; opacity: 0.6;
    background: linear-gradient(90deg, var(--a-cap-1) 50%, var(--a-cap-2) 50%);
}
.stApp::before { width: 200px; height: 74px; top: 6%;    right: 3%; transform: rotate(-28deg); }
.stApp::after  { width: 160px; height: 60px; bottom: 7%; left: 2%;  transform: rotate(32deg); }
.block-container {
    position: relative; z-index: 1;
    max-width: 1120px; padding-top: 2.8rem; padding-bottom: 2rem;
}

/* ---------- one big split card (left brand panel + right form) ---------- */
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch !important;
    background: var(--a-card);
    border: 1px solid var(--a-card-border);
    border-radius: 28px;
    overflow: hidden;
    box-shadow: var(--a-card-shadow);
}

/* left column = deep teal brand panel (same in both modes) */
[data-testid="stHorizontalBlock"] > div:first-child {
    position: relative; overflow: hidden;
    padding: 2.6rem 2.5rem;
    display: flex; flex-direction: column; justify-content: center;
    background:
        radial-gradient(520px 320px at 100% 0%, rgba(47,191,161,0.38), rgba(47,191,161,0) 70%),
        radial-gradient(420px 300px at 0% 100%, rgba(47,191,161,0.18), rgba(47,191,161,0) 70%),
        linear-gradient(165deg, #0B3D3A 0%, #0F5E56 60%, #147D71 100%);
}
/* two capsules bleeding off the panel corners */
[data-testid="stHorizontalBlock"] > div:first-child::before,
[data-testid="stHorizontalBlock"] > div:first-child::after {
    content: ""; position: absolute; border-radius: 999px; pointer-events: none;
    background: linear-gradient(90deg, #2FBFA1 50%, #F2FBF9 50%);
}
[data-testid="stHorizontalBlock"] > div:first-child::before {
    width: 150px; height: 54px; top: 26px; right: -30px;
    transform: rotate(-30deg);
    box-shadow: inset 0 -8px 14px rgba(0,0,0,0.14), inset 0 8px 12px rgba(255,255,255,0.35),
                0 16px 30px rgba(0,0,0,0.30);
    animation: spg-float 6s ease-in-out infinite;
}
[data-testid="stHorizontalBlock"] > div:first-child::after {
    width: 120px; height: 44px; bottom: -14px; left: -34px;
    transform: rotate(28deg); opacity: 0.22;
}
@keyframes spg-float {
    0%, 100% { transform: translateY(0)    rotate(-30deg); }
    50%      { transform: translateY(-9px) rotate(-30deg); }
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stHorizontalBlock"] > div:first-child::before { animation: none; }
}

/* right column = form panel */
[data-testid="stHorizontalBlock"] > div:last-child {
    padding: 2.6rem 2.7rem;
    display: flex; flex-direction: column; justify-content: center;
}

/* ---------- brand panel content ---------- */
.auth-brand { position: relative; z-index: 1; }
.auth-brand, .auth-brand * { color: #F2FBF9 !important; }
.auth-logo { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 2.6rem; }
.auth-logo-mark {
    width: 44px; height: 44px; border-radius: 13px;
    background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.24);
    display: flex; align-items: center; justify-content: center; font-size: 1.35rem;
}
.auth-logo-text b     { display: block; font-size: 1.25rem; font-weight: 800; line-height: 1.1; }
.auth-logo-text small { display: block; font-size: 0.78rem; opacity: 0.75; }
.auth-brand h1 {
    font-size: 2.15rem; font-weight: 800; line-height: 1.18; letter-spacing: -0.3px;
    margin: 0 0 0.9rem 0; color: #FFFFFF !important;
}
.auth-brand p.lead { font-size: 1rem; line-height: 1.6; opacity: 0.9; margin: 0 0 1.5rem 0; max-width: 40ch; }
.auth-feature {
    display: flex; align-items: center; gap: 0.85rem;
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
    border-radius: 14px; padding: 0.7rem 0.9rem; margin-bottom: 0.6rem;
}
.auth-feature .fi {
    flex: 0 0 38px; width: 38px; height: 38px; border-radius: 10px;
    background: rgba(47,191,161,0.25);
    display: flex; align-items: center; justify-content: center; font-size: 1.15rem;
}
.auth-feature b     { display: block; font-size: 0.94rem; font-weight: 700; }
.auth-feature small { display: block; font-size: 0.8rem; opacity: 0.78; line-height: 1.35; }
.auth-note {
    margin-top: 1.4rem; padding-top: 0.9rem; font-size: 0.8rem; opacity: 0.75;
    border-top: 1px solid rgba(255,255,255,0.18); line-height: 1.5;
}

/* ---------- form panel content ---------- */
.auth-title { font-size: 1.8rem; font-weight: 800; color: var(--a-title); letter-spacing: -0.2px; margin-bottom: 0.25rem; }
.auth-sub   { font-size: 0.95rem; color: var(--a-sub); margin-bottom: 1.4rem; }

/* tabs -> pill switch (removes Streamlit's red underline).
   Selectors cover both old (data-baseweb) and new (role="tab") Streamlit versions. */
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }
[role="tablist"]::before,
[role="tablist"]::after { display: none !important; }
[role="tablist"] {
    gap: 4px; padding: 5px; background: var(--a-tab-bg) !important; border-radius: 14px;
    border: none !important; box-shadow: none !important;
}
[role="tablist"] button[role="tab"] {
    flex: 1; height: 44px; justify-content: center;
    border-radius: 10px; background: transparent !important;
    border: none !important; box-shadow: none !important;
}
[role="tablist"] button[role="tab"]::before,
[role="tablist"] button[role="tab"]::after { display: none !important; }
/* tab text colour: this is what was invisible (white on white) */
[role="tablist"] button[role="tab"],
[role="tablist"] button[role="tab"] * {
    color: var(--a-tab-text) !important; font-weight: 700; font-size: 0.97rem;
}
[role="tablist"] button[role="tab"][aria-selected="true"] {
    background: var(--a-tab-active-bg) !important; box-shadow: var(--a-tab-shadow) !important;
}
[role="tablist"] button[role="tab"][aria-selected="true"],
[role="tablist"] button[role="tab"][aria-selected="true"] * { color: var(--a-tab-active-text) !important; }
[role="tabpanel"], [data-baseweb="tab-panel"] { padding-top: 1.3rem; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

/* inputs (selectors cover old + new Streamlit) */
[data-testid="stWidgetLabel"] p,
[data-testid="stTextInput"] label p { color: var(--a-label) !important; font-weight: 600; font-size: 0.9rem; }
[data-testid="stTextInputRootElement"],
div[data-baseweb="input"] {
    background: var(--a-input-bg) !important;
    border: 1.5px solid var(--a-input-border) !important;
    border-radius: 12px !important;
    min-height: 48px;
    box-shadow: none !important;
    transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}
[data-testid="stTextInputRootElement"]:focus-within,
div[data-baseweb="input"]:focus-within {
    background: var(--a-input-focus-bg) !important;
    border-color: #2FBFA1 !important;
    box-shadow: 0 0 0 4px rgba(47,191,161,0.18) !important;
}
/* inner wrappers: no second background / second border */
[data-testid="stTextInputRootElement"] > div,
[data-testid="stTextInputRootElement"] div[data-baseweb="base-input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] input {
    background: transparent !important; border: none !important; box-shadow: none !important;
    color: var(--a-input-text) !important; -webkit-text-fill-color: var(--a-input-text) !important;
    caret-color: var(--a-caret); font-size: 0.97rem; padding: 0.7rem 0.9rem;
}
[data-testid="stTextInput"] input::placeholder {
    color: var(--a-placeholder) !important; -webkit-text-fill-color: var(--a-placeholder) !important; opacity: 1;
}
/* browser autofill (saved passwords) would otherwise paint its own colour */
[data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stTextInput"] input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px var(--a-input-bg) inset !important;
    -webkit-text-fill-color: var(--a-input-text) !important;
    caret-color: var(--a-caret);
    transition: background-color 9999s ease-out 0s;
}
/* show/hide password (eye) button */
[data-testid="stTextInputRootElement"] button { background: transparent !important; border: none !important; }
[data-testid="stTextInputRootElement"] button svg { fill: var(--a-icon) !important; color: var(--a-icon) !important; }

/* main action button (same teal in both modes) */
[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-secondaryFormSubmit"],
button[kind="secondaryFormSubmit"] {
    width: 100%; height: 3.1rem; margin-top: 0.4rem;
    background: linear-gradient(135deg, #147D71 0%, #0F5E56 100%) !important;
    border: none !important; border-radius: 12px !important;
    box-shadow: 0 10px 20px rgba(15,94,86,0.28) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
[data-testid="stFormSubmitButton"] button p,
button[data-testid="stBaseButton-secondaryFormSubmit"] p { color: #FFFFFF !important; font-weight: 700; font-size: 1rem; }
[data-testid="stFormSubmitButton"] button:hover,
button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
    background: linear-gradient(135deg, #0F5E56 0%, #0B3D3A 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 14px 26px rgba(15,94,86,0.34) !important;
}
[data-testid="stFormSubmitButton"] button:focus-visible {
    outline: 3px solid rgba(47,191,161,0.55); outline-offset: 2px;
}

[data-testid="stAlert"] { border-radius: 12px; }

.auth-trust {
    margin-top: 1.2rem; padding: 0.75rem 0.95rem;
    background: var(--a-trust-bg); border-radius: 12px;
    font-size: 0.82rem; line-height: 1.45; color: var(--a-trust-text);
}
.stApp .spg-disclaimer { text-align: center; border-top: none; margin-top: 1.4rem; }

/* ---------- phones and small tablets: stack the two panels ---------- */
@media (max-width: 800px) {
    .block-container { padding: 1rem 0.8rem 1.5rem 0.8rem; }
    .stApp::before, .stApp::after { display: none; }
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important; flex-wrap: nowrap !important;
        border-radius: 22px;
    }
    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important; min-width: 100% !important; flex: 0 0 auto !important;
    }
    [data-testid="stHorizontalBlock"] > div:first-child,
    [data-testid="stHorizontalBlock"] > div:last-child { padding: 1.6rem 1.4rem; }
    [data-testid="stHorizontalBlock"] > div:first-child::before {
        width: 108px; height: 40px; top: 18px; right: -22px;
    }
    [data-testid="stHorizontalBlock"] > div:first-child::after { display: none; }
    .auth-logo { margin-bottom: 1.4rem; }
    .auth-brand h1 { font-size: 1.55rem; margin-bottom: 0; }
    .auth-brand p.lead, .auth-feature, .auth-note { display: none; }
    .auth-title { font-size: 1.5rem; }
}
</style>
"""


def _feature(icon: str, title: str, text: str) -> str:
    return (
        f'<div class="auth-feature"><span class="fi">{icon}</span>'
        f"<div><b>{title}</b><small>{text}</small></div></div>"
    )


BRAND_HTML = (
    '<div class="auth-brand">'
    '<div class="auth-logo"><span class="auth-logo-mark">💊</span>'
    '<div class="auth-logo-text"><b>SPG</b><small>Smart Pharma Guider</small></div></div>'
    "<h1>Know your medicines before you take them.</h1>"
    '<p class="lead">Plain-language answers about food interactions, missed doses, '
    "storage and alternatives, so you can ask your pharmacist better questions.</p>"
    + _feature("🍽️", "Food and drink checks", "See how a medicine reacts with what you eat")
    + _feature("⏰", "Missed dose guidance", "Know what to do when you forget a dose")
    + _feature("🔄", "Alternative options", "Compare other medicines and what differs")
    + _feature("🧊", "Storage and handling", "Keep your medicine safe and effective")
    + '<div class="auth-note">Answers are general education only. They are not a '
    "diagnosis and do not replace your doctor or pharmacist.</div>"
    "</div>"
)

SIDEBAR_USER_CSS = """
<style>
.user-card {
    display: flex; align-items: center; gap: 0.7rem;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    padding: 0.65rem 0.8rem;
    margin: 0.9rem 0 0.6rem 0;
}
section[data-testid="stSidebar"] .user-avatar {
    flex: 0 0 38px; width: 38px; height: 38px; border-radius: 50%;
    background: var(--spg-accent);
    color: #0B3D3A !important;
    font-weight: 800; font-size: 1.05rem;
    display: flex; align-items: center; justify-content: center;
}
.user-meta { min-width: 0; }
.user-name { font-weight: 700; font-size: 0.92rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-mail { font-size: 0.75rem; opacity: 0.75; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
"""


# ------------------------------------------------------------------
# SIGN IN / SIGN UP FORMS
# ------------------------------------------------------------------
def _sign_in_form():
    with st.form("signin_form"):
        email = st.text_input("✉️  Email address", placeholder="you@example.com", key="si_email")
        password = st.text_input(
            "🔒  Password", type="password", placeholder="Your password", key="si_password"
        )
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if not submitted:
        return

    wait = _locked_seconds()
    if wait:
        st.error(f"Too many failed attempts. Try again in {wait} seconds.")
        return

    email = email.strip().lower()
    if not email or not password:
        st.warning("Enter your email and password to sign in.")
        return

    user = verify_user(email, password)
    if user is None:
        _register_failure()
        st.error("Email or password is incorrect. Check both and try again.")
        return

    _log_in(user)


def _sign_up_form():
    with st.form("signup_form"):
        name = st.text_input("👤  Full name", placeholder="e.g. Ayesha Khan", key="su_name")
        email = st.text_input("✉️  Email address", placeholder="you@example.com", key="su_email")
        password = st.text_input(
            "🔒  Password",
            type="password",
            placeholder=f"At least {MIN_PASSWORD_LEN} characters",
            key="su_password",
        )
        confirm = st.text_input(
            "🔒  Confirm password",
            type="password",
            placeholder="Type your password again",
            key="su_confirm",
        )
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if not submitted:
        return

    name = " ".join(name.split())
    email = email.strip().lower()

    if not name or not email or not password or not confirm:
        st.warning("Fill in all four fields to create your account.")
    elif len(name) < 2 or len(name) > MAX_NAME_LEN:
        st.warning(f"Enter your full name (2 to {MAX_NAME_LEN} characters).")
    elif not EMAIL_RE.match(email):
        st.warning("Enter a valid email address, like you@example.com.")
    elif len(password) < MIN_PASSWORD_LEN:
        st.warning(f"Your password needs at least {MIN_PASSWORD_LEN} characters.")
    elif len(password) > MAX_PASSWORD_LEN:
        st.warning(f"Your password can be at most {MAX_PASSWORD_LEN} characters.")
    elif password != confirm:
        st.warning("The two passwords don't match. Type them again.")
    elif not create_user(name, email, password):
        st.error("An account with this email already exists. Use the Sign in tab instead.")
    else:
        _log_in({"name": name, "email": email})


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------
def _render_auth_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    left, right = st.columns(2, gap="small")

    with left:
        st.markdown(BRAND_HTML, unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="auth-title">Welcome to SPG</div>'
            '<div class="auth-sub">Sign in to continue, or create a new account.</div>',
            unsafe_allow_html=True,
        )
        tab_in, tab_up = st.tabs(["Sign in", "Create account"])
        with tab_in:
            _sign_in_form()
        with tab_up:
            _sign_up_form()
        st.markdown(
            '<div class="auth-trust">🔒 Your password is salted and hashed. '
            "SPG never stores it as plain text.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="spg-disclaimer">In a medical emergency, contact your local '
        "emergency number immediately.</div>",
        unsafe_allow_html=True,
    )


def require_login() -> dict:
    """Call once, right after the CSS is injected in app.py."""
    # Dark-mode colours for the app. Must run on every rerun, whether the
    # user is logged in or not, so it comes before the login check.
    st.markdown(APP_THEME_CSS, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if user:
        return user
    _render_auth_page()
    st.stop()


def render_sidebar_user():
    """Call inside `with st.sidebar:` to show the user card and Log out."""
    user = st.session_state.get("user")
    if not user:
        return

    name = html.escape(user["name"])
    mail = html.escape(user["email"])
    initial = html.escape(user["name"][:1].upper())

    st.markdown(SIDEBAR_USER_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="user-card"><div class="user-avatar">{initial}</div>'
        f'<div class="user-meta"><div class="user-name">{name}</div>'
        f'<div class="user-mail">{mail}</div></div></div>',
        unsafe_allow_html=True,
    )
    if st.button("Log out", key="logout_btn", use_container_width=True):
        logout()