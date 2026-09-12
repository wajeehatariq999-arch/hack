# 💊 SPG — Smart Pharma Guider

SPG is an AI-powered pharmacy information assistant built with **Python
+ Streamlit** and the **Google Gemini API** (current official
`google-genai` SDK). It provides general, educational medicine
information across five focused features, with a two-stage
relevance/safety pipeline in front of every AI answer.

> ⚠️ SPG is an educational tool only. It never diagnoses, never
> prescribes, and never replaces a licensed doctor or pharmacist.

---

## 1. Features

1. **Food–Medicine Interaction** — checks possible interactions between a medicine and a food/drink/supplement.
2. **Missed Dose Guide** — general, medicine-specific guidance after a missed dose (never "just double it").
3. **Alternative Options** — discusses possible alternative categories/medicines and key differences.
4. **Storage & Handling** — storage and handling guidance for a specific medicine.
5. **Quick Self-Assessment** — general educational guidance based on symptoms, with red flags and next steps (never a diagnosis).

Every feature is powered dynamically by Gemini using the user's actual
input — there are no hard-coded medical answers anywhere in the app.

---

## 2. Project Structure

```
SPG/
├── app.py                       # Main Streamlit app: UI, navigation, pages
├── ai_service.py                 # Gemini API client + error handling
├── prompts.py                    # All system instructions / prompt templates
├── safety.py                     # Relevance + emergency two-stage checks
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── .gitignore                    # Protects secrets.toml from GitHub
└── .streamlit/
    ├── secrets.toml               # YOUR real API key goes here (never commit)
    └── secrets.toml.example       # Safe template to commit to GitHub
```

### What each file does

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI: page config, custom teal/green CSS theme, sidebar navigation, hero/home page, and the five feature pages (forms, spinners, result cards). |
| `ai_service.py` | Creates the Gemini client from your secret key, and handles all calls to the Gemini API (both the safety classifier calls and the final answer generation), converting any failure into a friendly message. |
| `prompts.py` | Central library of every AI instruction: global safety rules, the relevance-check prompt, the emergency-check prompt, and one dedicated system prompt per feature. |
| `safety.py` | Implements Stage 1 (relevance check) and Stage 2 (emergency check) using Gemini, plus a local emergency-keyword safety net used only if the AI call itself fails. |
| `requirements.txt` | Lists `streamlit` and `google-genai` so `pip install -r requirements.txt` sets everything up. |
| `.streamlit/secrets.toml` | Where your **real** Gemini API key goes. This file is git-ignored. |
| `.streamlit/secrets.toml.example` | A safe template you commit to GitHub instead, so collaborators know the expected format. |
| `.gitignore` | Makes sure `secrets.toml` (and other real API keys) never get pushed to GitHub. |

---

## 3. Where to Put Your Gemini API Key

1. Get a free Gemini API key from **Google AI Studio**: https://aistudio.google.com/apikey
2. Open `SPG/.streamlit/secrets.toml`
3. Replace the placeholder with your real key:

```toml
GEMINI_API_KEY = "your-real-key-goes-here"
```

4. Save the file. **Never** paste your real key into any `.py` file, and never remove `secrets.toml` from `.gitignore`.

---

## 4. Beginner-Friendly Local Setup

**Step 1 — Install Python**
Make sure you have Python 3.10 or newer installed (check with `python --version` or `python3 --version`).

**Step 2 — Get the project folder**
Place the entire `SPG/` folder on your computer (all files above should be inside it).

**Step 3 — Open a terminal inside the `SPG` folder**

```bash
cd path/to/SPG
```

**Step 4 — (Recommended) Create a virtual environment**

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

**Step 5 — Install the dependencies**

```bash
pip install -r requirements.txt
```

**Step 6 — Add your API key**
Edit `.streamlit/secrets.toml` as described in Section 3 above.

---

## 5. How to Run the App

From inside the `SPG` folder, with your virtual environment activated:

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) —
open it in your browser. The sidebar will show a green
"Gemini API key detected ✅" badge once your key is set up correctly;
if you see a yellow warning instead, double-check Section 3.

---

## 6. How to Test All Five Features

Try each of these example inputs to confirm everything works end to end:

1. **Food–Medicine Interaction**
   - Medicine: `Warfarin`
   - Food/drink: `Grapefruit juice`
   - Expect: an explanation of the interaction, why it matters, and precautions.

2. **Missed Dose Guide**
   - Medicine: `Metformin`
   - Situation: `I forgot my afternoon dose, it's 3 hours late, next dose is in 5 hours`
   - Expect: general guidance, a clear warning against doubling doses.

3. **Alternative Options**
   - Medicine: `Ibuprofen`
   - Reason: `It upsets my stomach`
   - Expect: possible alternative categories and a safety note about consulting a professional.

4. **Storage & Handling**
   - Medicine: `Insulin`
   - Expect: general storage guidance (e.g. refrigeration notes) and a disposal note.

5. **Quick Self-Assessment**
   - Symptoms: `Mild headache and sore throat for 2 days, no fever`
   - Expect: general educational information, red flags, and next steps — no diagnosis.

**Also test the safety pipeline:**
- Type something unrelated like `"Who won the cricket world cup?"` in any feature → SPG should politely refuse (not-relevant message).
- Type something like `"I think I'm having a severe allergic reaction and can't breathe"` → SPG should immediately show the red emergency banner instead of a normal answer.

**Also test error handling:**
- Temporarily put a wrong value in `secrets.toml` → the sidebar should show the warning badge, and submitting a form should show a clear "invalid API key" message instead of crashing.

---

## 7. GitHub Upload Steps

1. Initialize a git repository inside the `SPG` folder (if not already done):
   ```bash
   git init
   ```
2. Confirm `.gitignore` is present (it already excludes `secrets.toml`).
3. Stage and commit everything:
   ```bash
   git add .
   git commit -m "Initial commit: SPG - Smart Pharma Guider"
   ```
4. Create a new empty repository on GitHub (do **not** initialize it with a README, so it stays empty).
5. Link and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```
6. Double-check on GitHub.com that `.streamlit/secrets.toml` was **not** uploaded — only `secrets.toml.example` should be visible.

---

## 8. Streamlit Cloud Deployment Steps

1. Go to https://share.streamlit.io and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository, the branch (e.g. `main`), and set the main file path to `app.py`.
4. Click **"Deploy"** — it will fail once at first launch because no API key is configured yet; that's expected.

---

## 9. Exactly Where to Add `GEMINI_API_KEY` in Streamlit Cloud Secrets

1. On your deployed app's page, click the **"⋮" (three dots) menu** → **"Settings"**.
2. Go to the **"Secrets"** tab.
3. Paste the following (with your real key):
   ```toml
   GEMINI_API_KEY = "your-real-key-goes-here"
   ```
4. Click **"Save"**. Streamlit Cloud will automatically restart your app with the key available as `st.secrets["GEMINI_API_KEY"]`.

---

## 10. Final Deployment Checklist

- [ ] `secrets.toml` contains a real, working Gemini API key (locally)
- [ ] `secrets.toml` is **not** committed to GitHub (only `secrets.toml.example` is)
- [ ] `pip install -r requirements.txt` completes with no errors
- [ ] `streamlit run app.py` launches with no errors
- [ ] Sidebar shows "Gemini API key detected ✅"
- [ ] All five features return real, dynamic Gemini-generated answers
- [ ] Unrelated questions (e.g. cricket) are politely refused
- [ ] Emergency-style input triggers the red emergency banner
- [ ] Invalid/missing API key shows a friendly error, not a crash
- [ ] GitHub repository is pushed with secrets excluded
- [ ] Streamlit Cloud Secrets contain the real `GEMINI_API_KEY`
- [ ] Deployed app link works and behaves the same as local

---

## Disclaimer

SPG (Smart Pharma Guider) provides general, AI-generated educational
information about medicines. It is **not** a medical device, does
**not** diagnose conditions, and does **not** replace professional
medical or pharmacist advice. In a medical emergency, contact your
local emergency number immediately.
