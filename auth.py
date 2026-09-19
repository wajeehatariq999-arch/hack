"""
auth.py
------------------------------------------------------------
SPG - Smart Pharma Guider
Sign Up / Sign In system.

- Users are stored in a local SQLite file (users.db).
- Passwords are never stored as plain text: each one is salted and
  hashed with PBKDF2-HMAC-SHA256.
- Uses only the Python standard library + Streamlit, so
  requirements.txt does not change.

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
# STYLES
# ------------------------------------------------------------------
AUTH_CSS = """
<style>
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

.block-container { max-width: 1080px; padding-top: 2.6rem; }

.auth-brand {
    background: linear-gradient(160deg, var(--spg-teal-dark) 0%, var(--spg-teal) 100%);
    border-radius: 20px;
    padding: 2.6rem 2.3rem;
    min-height: 590px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 10px 30px rgba(11,61,58,0.25);
}
.auth-brand, .auth-brand * { color: #F2FBF9 !important; }
.auth-capsule {
    width: 150px; height: 56px;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--spg-accent) 50%, #F2FBF9 50%);
    transform: rotate(-24deg);
    margin: 0.4rem 0 2.6rem 0.4rem;
    box-shadow: 0 12px 24px rgba(0,0,0,0.25);
}
.auth-brand h1 {
    font-size: 2rem; font-weight: 800; line-height: 1.2;
    margin: 0 0 0.9rem 0; color: #FFFFFF !important;
}
.auth-brand p {
    font-size: 1rem; line-height: 1.6; opacity: 0.92; margin: 0 0 1.6rem 0;
}
.auth-brand ul { list-style: none; padding: 0; margin: 0 0 1.8rem 0; }
.auth-brand li {
    position: relative; padding-left: 1.4rem; margin-bottom: 0.65rem;
    font-size: 0.95rem;
}
.auth-brand li::before {
    content: ""; position: absolute; left: 0; top: 0.55em;
    width: 8px; height: 8px; border-radius: 50%; background: var(--spg-accent);
}
.auth-note { font-size: 0.8rem; opacity: 0.75; border-top: 1px solid rgba(255,255,255,0.18); padding-top: 0.9rem; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--spg-card);
    border: 1px solid #E3ECEA;
    border-radius: 20px;
    padding: 1.2rem 1.3rem 0.8rem 1.3rem;
    box-shadow: 0 4px 16px rgba(15,94,86,0.06);
}
[data-testid="stForm"] { border: none !important; padding: 0 !important; }

.auth-title { font-size: 1.6rem; font-weight: 800; color: var(--spg-teal-dark); margin-bottom: 0.2rem; }
.auth-sub { font-size: 0.92rem; color: var(--spg-muted); margin-bottom: 0.8rem; }

.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
.stTabs [data-baseweb="tab"] p { font-weight: 600; font-size: 0.98rem; }
.stTabs [aria-selected="true"] p { color: var(--spg-teal-mid) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--spg-teal-mid) !important; }

.stTextInput label p { font-weight: 600; color: var(--spg-text); font-size: 0.9rem; }
.stTextInput input:focus { border-color: var(--spg-accent) !important; box-shadow: 0 0 0 1px var(--spg-accent) !important; }

@media (max-width: 800px) {
    .auth-brand { min-height: auto; padding: 1.8rem 1.4rem; }
    .auth-capsule { margin-bottom: 1.6rem; }
}
</style>
"""

BRAND_HTML = (
    '<div class="auth-brand">'
    '<div class="auth-capsule"></div>'
    "<h1>Know your medicines before you take them.</h1>"
    "<p>SPG explains food interactions, missed doses, storage rules and "
    "alternatives in plain language, so you can ask your pharmacist better questions.</p>"
    "<ul>"
    "<li>Check a medicine against food, drinks and supplements</li>"
    "<li>Find out what to do after a missed dose</li>"
    "<li>Learn how to store and handle your medicine</li>"
    "</ul>"
    '<div class="auth-note">Answers are general education only. They are not a diagnosis '
    "and do not replace your doctor or pharmacist.</div>"
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
        email = st.text_input("Email", placeholder="you@example.com", key="si_email")
        password = st.text_input(
            "Password", type="password", placeholder="Your password", key="si_password"
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
        name = st.text_input("Full name", placeholder="e.g. Ayesha Khan", key="su_name")
        email = st.text_input("Email", placeholder="you@example.com", key="su_email")
        password = st.text_input(
            "Password",
            type="password",
            placeholder=f"At least {MIN_PASSWORD_LEN} characters",
            key="su_password",
        )
        confirm = st.text_input(
            "Confirm password",
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
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(BRAND_HTML, unsafe_allow_html=True)

    with right:
        with st.container(border=True):
            st.markdown(
                '<div class="auth-title">Welcome to SPG</div>'
                '<div class="auth-sub">Sign in to continue, or create an account.</div>',
                unsafe_allow_html=True,
            )
            tab_in, tab_up = st.tabs(["Sign in", "Create account"])
            with tab_in:
                _sign_in_form()
            with tab_up:
                _sign_up_form()

    st.markdown(
        '<div class="spg-disclaimer">In a medical emergency, contact your local '
        "emergency number immediately.</div>",
        unsafe_allow_html=True,
    )


def require_login() -> dict:
    """Call once, right after the CSS is injected in app.py."""
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