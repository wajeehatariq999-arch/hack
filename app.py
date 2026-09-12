"""
app.py
------------------------------------------------------------
SPG - Smart Pharma Guider
Main Streamlit application: page config, custom design system,
sidebar navigation, hero/home page, and the five feature pages.
------------------------------------------------------------
"""

import streamlit as st
from ai_service import run_feature

# ------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="SPG | Smart Pharma Guider",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# GLOBAL CUSTOM CSS - original deep teal/green healthcare theme
# ------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    :root {
        --spg-teal-dark: #0B3D3A;
        --spg-teal: #0F5E56;
        --spg-teal-mid: #147D71;
        --spg-teal-light: #E4F3F0;
        --spg-accent: #2FBFA1;
        --spg-bg: #F7FAF9;
        --spg-card: #FFFFFF;
        --spg-text: #16302C;
        --spg-muted: #5C7A75;
        --spg-danger: #C0392B;
        --spg-danger-bg: #FDECEA;
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--spg-text);
    }

    .stApp {
        background: var(--spg-bg);
    }

    #MainMenu, footer, header {visibility: hidden;}

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--spg-teal-dark) 0%, var(--spg-teal) 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #F2FBF9 !important;
    }
    section[data-testid="stSidebar"] .stButton>button {
        width: 100%;
        text-align: left;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.45rem;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255,255,255,0.16);
        border-color: var(--spg-accent);
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] .stButton>button:focus {
        box-shadow: 0 0 0 2px var(--spg-accent);
    }
    .sidebar-active > button {
        background: var(--spg-accent) !important;
        color: var(--spg-teal-dark) !important;
        font-weight: 700 !important;
    }
    .sidebar-brand {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-bottom: 0.1rem;
    }
    .sidebar-sub {
        font-size: 0.8rem;
        opacity: 0.8;
        margin-bottom: 1.4rem;
    }

    .hero {
        background: linear-gradient(120deg, var(--spg-teal-dark), var(--spg-teal-mid));
        border-radius: 20px;
        padding: 2.6rem 2.4rem;
        color: #F2FBF9;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 30px rgba(11,61,58,0.25);
    }
    .hero h1 {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: #FFFFFF;
    }
    .hero p {
        font-size: 1.05rem;
        max-width: 640px;
        opacity: 0.92;
        line-height: 1.55;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(47,191,161,0.18);
        border: 1px solid var(--spg-accent);
        color: #D6FFF4;
        border-radius: 999px;
        padding: 0.25rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
        letter-spacing: 0.3px;
    }

    .spg-card-wrap {
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-bottom: 1.4rem;
    }
    .spg-card {
        background: var(--spg-card);
        border-radius: 16px 16px 0 0;
        border: 1px solid #E3ECEA;
        border-bottom: none;
        padding: 1.5rem 1.5rem 1.1rem 1.5rem;
        box-shadow: 0 4px 16px rgba(15,94,86,0.06);
        min-height: 190px;
        display: flex;
        flex-direction: column;
        transition: box-shadow 0.15s ease;
    }
    .spg-card-wrap:hover .spg-card {
        box-shadow: 0 10px 24px rgba(15,94,86,0.14);
    }
    .spg-card .icon-badge {
        width: 46px;
        height: 46px;
        border-radius: 12px;
        background: var(--spg-teal-light);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        margin-bottom: 0.7rem;
    }
    .spg-card h3 {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        color: var(--spg-teal-dark);
        line-height: 1.3;
    }
    .spg-card p {
        font-size: 0.87rem;
        color: var(--spg-muted);
        line-height: 1.5;
        margin-bottom: 0;
    }
    .spg-card-wrap .stButton {
        margin-top: 0 !important;
    }
    .spg-card-wrap .stButton>button {
        width: 100%;
        border-radius: 0 0 16px 16px !important;
        border: 1px solid #E3ECEA !important;
        border-top: 1px dashed #D3E4E0 !important;
        background: var(--spg-teal-light) !important;
        color: var(--spg-teal-dark) !important;
        font-weight: 600;
        padding: 0.55rem 1rem !important;
        box-shadow: none !important;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .spg-card-wrap .stButton>button:hover {
        background: var(--spg-teal-mid) !important;
        color: #FFFFFF !important;
        transform: none !important;
    }

    .feature-header {
        background: var(--spg-teal-light);
        border-left: 5px solid var(--spg-teal-mid);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.4rem;
    }
    .feature-header h2 {
        margin: 0 0 0.25rem 0;
        color: var(--spg-teal-dark);
        font-size: 1.4rem;
        font-weight: 800;
    }
    .feature-header p {
        margin: 0;
        color: var(--spg-muted);
        font-size: 0.92rem;
    }

    .result-card {
        background: var(--spg-card);
        border: 1px solid #E3ECEA;
        border-left: 5px solid var(--spg-accent);
        border-radius: 14px;
        padding: 1.4rem 1.5rem;
        margin-top: 1.2rem;
        box-shadow: 0 4px 16px rgba(15,94,86,0.06);
        line-height: 1.6;
    }

    .emergency-card {
        background: var(--spg-danger-bg);
        border: 1px solid var(--spg-danger);
        border-left: 6px solid var(--spg-danger);
        border-radius: 14px;
        padding: 1.4rem 1.5rem;
        margin-top: 1.2rem;
        color: #7B241C;
        line-height: 1.6;
    }

    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div {
        border-radius: 10px !important;
        border: 1px solid #D3E4E0 !important;
    }

    div.stButton>button[kind="primary"], .main .stButton>button {
        background: var(--spg-teal-mid);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
    }
    .main .stButton>button:hover {
        background: var(--spg-teal-dark);
        transform: translateY(-1px);
    }

    .spg-disclaimer {
        font-size: 0.78rem;
        color: var(--spg-muted);
        border-top: 1px dashed #D3E4E0;
        margin-top: 1.6rem;
        padding-top: 0.8rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------
# NAVIGATION STATE
# ------------------------------------------------------------------
PAGES = {
    "home": "🏠 Home",
    "food_interaction": "🍽️ Food–Medicine Interaction",
    "missed_dose": "⏰ Missed Dose Guide",
    "alternative_options": "🔄 Alternative Options",
    "storage_handling": "🧊 Storage & Handling",
    "self_assessment": "🩺 Quick Self-Assessment",
}

if "page" not in st.session_state:
    st.session_state.page = "home"


def go_to(page_key: str):
    st.session_state.page = page_key


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">💊 SPG</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-sub">Smart Pharma Guider</div>',
        unsafe_allow_html=True,
    )

    for key, label in PAGES.items():
        active = st.session_state.page == key
        wrapper_class = "sidebar-active" if active else ""
        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            go_to(key)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(
        '<div class="spg-disclaimer">SPG provides general educational '
        "information only and is not a substitute for professional "
        "medical or pharmacist advice.</div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# SHARED RESULT RENDERING
# ------------------------------------------------------------------
def render_result(result: dict):
    status = result.get("status")
    message = result.get("message", "")

    if status == "emergency":
        st.markdown(f'<div class="emergency-card">{message}</div>', unsafe_allow_html=True)
    elif status == "not_relevant":
        st.info(message)
    elif status == "error":
        st.error(message)
    elif status == "ok":
        st.markdown(f'<div class="result-card">{message}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="spg-disclaimer">This is general educational '
            "information generated by AI, not a diagnosis or a "
            "prescription. Please confirm important decisions with a "
            "licensed doctor or pharmacist.</div>",
            unsafe_allow_html=True,
        )


def feature_header(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="feature-header">
            <h2>{icon} {title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# HOME PAGE
# ------------------------------------------------------------------
def render_home():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">AI-POWERED PHARMACY ASSISTANT</div>
            <h1>Smart Pharma Guider (SPG)</h1>
            <p>
                SPG helps you understand your medicines with confidence.
                Ask about food interactions, missed doses, alternatives,
                storage, or get a quick educational self-assessment of
                your symptoms — all explained clearly, safely, and in
                plain English. SPG never replaces your doctor or
                pharmacist, but it helps you ask them better questions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Choose a feature to get started")

    cards = [
        ("food_interaction", "🍽️", "Food–Medicine Interaction",
         "Check how a medicine might interact with a food, drink, or supplement."),
        ("missed_dose", "⏰", "Missed Dose Guide",
         "Get general guidance on what to do if you missed a dose."),
        ("alternative_options", "🔄", "Alternative Options",
         "Explore possible alternatives to a medicine and key differences."),
        ("storage_handling", "🧊", "Storage & Handling",
         "Learn how to properly store and handle a specific medicine."),
        ("self_assessment", "🩺", "Quick Self-Assessment",
         "Describe your symptoms for general educational guidance and red flags."),
    ]

    row1 = st.columns(3)
    row2 = st.columns(3)
    cols = row1 + row2

    for col, (key, icon, title, desc) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="spg-card-wrap">
                <div class="spg-card">
                    <div class="icon-badge">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open →", key=f"open_{key}", use_container_width=True):
                go_to(key)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="spg-disclaimer">⚠️ SPG is an educational tool only. '
        "It does not diagnose conditions, prescribe medicines, or "
        "replace professional healthcare. In a medical emergency, "
        "contact your local emergency number immediately.</div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# FEATURE 1: FOOD-MEDICINE INTERACTION
# ------------------------------------------------------------------
def render_food_interaction():
    feature_header(
        "🍽️", "Food–Medicine Interaction",
        "Find out how a medicine might interact with a food, drink, or supplement.",
    )

    with st.form("food_interaction_form"):
        medicine = st.text_input("Medicine name*", placeholder="e.g. Warfarin")
        food = st.text_input("Food / drink / supplement*", placeholder="e.g. Grapefruit juice")
        extra = st.text_area(
            "Anything else you'd like to add? (optional)",
            placeholder="e.g. I take it every morning with breakfast",
        )
        submitted = st.form_submit_button("Check Interaction", use_container_width=True)

    if submitted:
        if not medicine.strip() or not food.strip():
            st.warning("Please enter both the medicine name and the food/drink.")
            return

        raw_text = f"Medicine: {medicine}. Food/drink: {food}. Extra info: {extra}"
        user_prompt = (
            f"Medicine: {medicine}\n"
            f"Food/Drink/Supplement: {food}\n"
            f"Additional context from user: {extra if extra.strip() else 'None'}\n\n"
            "Explain the possible interaction between this medicine and this "
            "food/drink/supplement following your instructed structure."
        )
        with st.spinner("Checking possible interactions..."):
            result = run_feature("food_interaction", user_prompt, raw_text)
        render_result(result)


# ------------------------------------------------------------------
# FEATURE 2: MISSED DOSE GUIDE
# ------------------------------------------------------------------
def render_missed_dose():
    feature_header(
        "⏰", "Missed Dose Guide",
        "Get general guidance on what to do after missing a dose of your medicine.",
    )

    with st.form("missed_dose_form"):
        medicine = st.text_input("Medicine name*", placeholder="e.g. Metformin")
        situation = st.text_area(
            "Describe the missed-dose situation*",
            placeholder="e.g. I forgot my afternoon dose and it's now 4 hours late. My next dose is in 3 hours.",
        )
        submitted = st.form_submit_button("Get Guidance", use_container_width=True)

    if submitted:
        if not medicine.strip() or not situation.strip():
            st.warning("Please enter the medicine name and describe the situation.")
            return

        raw_text = f"Medicine: {medicine}. Missed dose situation: {situation}"
        user_prompt = (
            f"Medicine: {medicine}\n"
            f"Missed-dose situation described by user: {situation}\n\n"
            "Provide medicine-specific general guidance following your "
            "instructed structure. Do not tell the user to automatically "
            "double the next dose."
        )
        with st.spinner("Preparing guidance..."):
            result = run_feature("missed_dose", user_prompt, raw_text)
        render_result(result)


# ------------------------------------------------------------------
# FEATURE 3: ALTERNATIVE OPTIONS
# ------------------------------------------------------------------
def render_alternative_options():
    feature_header(
        "🔄", "Alternative Options",
        "Explore possible alternatives to a medicine and understand key differences.",
    )

    with st.form("alternative_options_form"):
        medicine = st.text_input("Current medicine*", placeholder="e.g. Ibuprofen")
        reason = st.text_area(
            "Reason you're looking for an alternative*",
            placeholder="e.g. It upsets my stomach / it's unavailable at my pharmacy / cost concerns",
        )
        submitted = st.form_submit_button("Explore Alternatives", use_container_width=True)

    if submitted:
        if not medicine.strip() or not reason.strip():
            st.warning("Please enter the current medicine and your reason for an alternative.")
            return

        raw_text = f"Medicine: {medicine}. Reason for alternative: {reason}"
        user_prompt = (
            f"Current medicine: {medicine}\n"
            f"Reason for wanting an alternative: {reason}\n\n"
            "Discuss possible alternatives/categories and important "
            "differences, following your instructed structure. Do not "
            "casually tell the user to just replace their prescribed "
            "medicine."
        )
        with st.spinner("Exploring alternatives..."):
            result = run_feature("alternative_options", user_prompt, raw_text)
        render_result(result)


# ------------------------------------------------------------------
# FEATURE 4: STORAGE & HANDLING
# ------------------------------------------------------------------
def render_storage_handling():
    feature_header(
        "🧊", "Storage & Handling",
        "Learn how to properly store and handle a specific medicine.",
    )

    with st.form("storage_handling_form"):
        medicine = st.text_input("Medicine name*", placeholder="e.g. Insulin")
        context = st.text_area(
            "Any specific context? (optional)",
            placeholder="e.g. I'm traveling for a week / I live somewhere hot",
        )
        submitted = st.form_submit_button("Get Storage Guidance", use_container_width=True)

    if submitted:
        if not medicine.strip():
            st.warning("Please enter a medicine name.")
            return

        raw_text = f"Medicine: {medicine}. Context: {context}"
        user_prompt = (
            f"Medicine: {medicine}\n"
            f"Additional context from user: {context if context.strip() else 'None'}\n\n"
            "Provide appropriate storage and handling guidance following "
            "your instructed structure. If you are uncertain about exact "
            "details for this medicine, say so clearly."
        )
        with st.spinner("Looking up storage guidance..."):
            result = run_feature("storage_handling", user_prompt, raw_text)
        render_result(result)


# ------------------------------------------------------------------
# FEATURE 5: QUICK SELF-ASSESSMENT
# ------------------------------------------------------------------
def render_self_assessment():
    feature_header(
        "🩺", "Quick Self-Assessment",
        "Describe your symptoms for general educational guidance. This does not diagnose you.",
    )

    with st.form("self_assessment_form"):
        symptoms = st.text_area(
            "Describe your symptoms*",
            placeholder="e.g. Mild headache and sore throat for 2 days, no fever",
        )
        details = st.text_area(
            "Relevant details (optional)",
            placeholder="e.g. Age range, how long it's lasted, any medicine already taken",
        )
        submitted = st.form_submit_button("Get Educational Guidance", use_container_width=True)

    if submitted:
        if not symptoms.strip():
            st.warning("Please describe your symptoms.")
            return

        raw_text = f"Symptoms: {symptoms}. Details: {details}"
        user_prompt = (
            f"Symptoms described by user: {symptoms}\n"
            f"Additional relevant details: {details if details.strip() else 'None'}\n\n"
            "Provide general educational guidance, possible concerns, red "
            "flags, and appropriate next steps following your instructed "
            "structure. Do not diagnose."
        )
        with st.spinner("Preparing general guidance..."):
            result = run_feature("self_assessment", user_prompt, raw_text)
        render_result(result)


# ------------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------------
ROUTES = {
    "home": render_home,
    "food_interaction": render_food_interaction,
    "missed_dose": render_missed_dose,
    "alternative_options": render_alternative_options,
    "storage_handling": render_storage_handling,
    "self_assessment": render_self_assessment,
}

ROUTES.get(st.session_state.page, render_home)()