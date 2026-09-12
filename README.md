<div align="center">

# 💊 SPG — Smart Pharma Guider

### Your AI-Powered Pocket Pharmacy Assistant

*Understand your medicines with confidence — safely, clearly, and instantly.*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini_API-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)
![Status](https://img.shields.io/badge/Status-Deployment_Ready-2FBFA1?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational_Use-0F5E56?style=for-the-badge)

</div>

---

## 📖 Table of Contents

1. [About the Project](#-about-the-project)
2. [Features](#-features)
3. [How the Safety Pipeline Works](#-how-the-safety-pipeline-works)
4. [Tech Stack](#-tech-stack)
5. [Project Structure](#-project-structure)
6. [Where to Put Your Gemini API Key](#-where-to-put-your-gemini-api-key)
7. [Local Setup (Beginner-Friendly)](#-local-setup-beginner-friendly)
8. [Running the App](#-running-the-app)
9. [Testing All Five Features](#-testing-all-five-features)
10. [GitHub Upload Guide](#-github-upload-guide)
11. [Streamlit Cloud Deployment Guide](#-streamlit-cloud-deployment-guide)
12. [Final Deployment Checklist](#-final-deployment-checklist)
13. [Disclaimer](#-disclaimer)

---

## 🧭 About the Project

**SPG (Smart Pharma Guider)** is a full-stack, AI-powered pharmacy
information assistant built for a hackathon submission. It combines a
polished **Streamlit** front end with the **Google Gemini API** to turn
plain-English questions about medicines into clear, structured,
educational answers — instantly.

Every single answer in SPG is generated **dynamically** by Gemini based
on the user's real input. There are no hidden dictionaries, no
hard-coded drug facts, and no canned responses — just a carefully
engineered AI pipeline with safety guardrails built in from the ground
up.

> **Why it matters:** People often have quick medicine questions —
> *"Can I take this with milk?"*, *"I forgot my dose, now what?"* — but
> don't always have time to call a pharmacist. SPG bridges that gap
> with fast, structured, general education, while always pointing
> people back to real healthcare professionals for anything serious.

---

## ✨ Features

<table>
<tr>
<td width="20%" align="center">🍽️<br><b>Food–Medicine<br>Interaction</b></td>
<td>Checks possible interactions between a specific medicine and a food, drink, or supplement — explaining the risk, why it matters, and practical precautions.</td>
</tr>
<tr>
<td align="center">⏰<br><b>Missed Dose<br>Guide</b></td>
<td>Gives general, medicine-specific guidance after a missed dose — and explicitly warns against "just doubling up" without professional advice.</td>
</tr>
<tr>
<td align="center">🔄<br><b>Alternative<br>Options</b></td>
<td>Explores possible alternative medicines or categories based on the user's reason, along with key differences to be aware of.</td>
</tr>
<tr>
<td align="center">🧊<br><b>Storage &<br>Handling</b></td>
<td>Explains how to properly store and handle a specific medicine, including signs it may have gone bad and safe disposal notes.</td>
</tr>
<tr>
<td align="center">🩺<br><b>Quick Self-<br>Assessment</b></td>
<td>Takes symptoms and details and returns general educational guidance, red flags to watch for, and sensible next steps — <b>never</b> a diagnosis.</td>
</tr>
</table>

---

## 🛡️ How the Safety Pipeline Works

Every single request — no matter which feature — passes through a
**two-stage protection pipeline** before Gemini is allowed to generate
a final answer:

```
 User Input
     │
     ▼
┌───────────────────────────┐
│ STAGE 1 — Relevance Check  │   Is this actually about medicine,
│        (via Gemini)        │   pharmacy, or healthcare?
└─────────────┬───────────────┘
              │  ✅ relevant
              ▼
┌───────────────────────────┐
│ STAGE 2 — Emergency Check  │   Does this describe a possible
│  (Gemini + keyword net)    │   medical emergency?
└─────────────┬───────────────┘
              │  ✅ not an emergency
              ▼
┌───────────────────────────┐
│  Feature-Specific Answer   │   Gemini answers using a dedicated
│       (via Gemini)         │   system prompt for this feature only
└───────────────────────────┘
```

- 🚫 **Off-topic questions** (cricket, politics, coding, etc.) are
  politely refused — SPG stays 100% focused on health and medicine.
- 🚨 **Emergency situations** (overdose, poisoning, difficulty
  breathing, severe allergic reaction, etc.) immediately trigger a
  red warning banner urging the user to contact real emergency
  services — the AI never tries to "handle" an emergency itself.
- 🧯 The emergency check has a **local keyword safety net** as a
  backup, so a genuine red-flag phrase is still caught even if the
  Gemini API call itself fails.

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io) with a fully custom teal/green CSS theme |
| AI Engine | [Google Gemini API](https://ai.google.dev) via the official `google-genai` SDK |
| Language | Python 3.10+ |
| Secrets Management | Streamlit Secrets (`.streamlit/secrets.toml`) |
| Deployment Target | Streamlit Community Cloud |

---

## 📁 Project Structure

```
SPG/
├── app.py                       # Main Streamlit app: UI, navigation, all 5 pages
├── ai_service.py                # Gemini API client + robust error handling
├── prompts.py                   # Every system instruction / prompt template
├── safety.py                    # Two-stage relevance + emergency checks
├── requirements.txt             # Python dependencies
├── README.md                    # You are here 👋
├── .gitignore                   # Keeps secrets.toml out of GitHub
└── .streamlit/
    ├── secrets.toml             # 🔑 YOUR real API key goes here (never commit)
    └── secrets.toml.example     # Safe template that IS committed
```

<details>
<summary><b>📄 Click to see what each file does</b></summary>
<br>

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI: page config, custom design system, sidebar navigation, hero/home page, and the five feature pages (forms, spinners, result cards). |
| `ai_service.py` | Creates the Gemini client from your secret key and handles every API call — including converting rate limits, invalid keys, timeouts, and empty responses into friendly, human-readable messages. |
| `prompts.py` | A central library of every AI instruction: global safety rules, the relevance-check prompt, the emergency-check prompt, and one dedicated system prompt per feature so the five features never overlap. |
| `safety.py` | Implements Stage 1 (relevance) and Stage 2 (emergency) checks using Gemini, plus a local emergency-keyword safety net used only if the AI classification call itself fails. |
| `requirements.txt` | Lists `streamlit` and `google-genai` so one `pip install` sets everything up. |
| `.streamlit/secrets.toml` | Where your **real** Gemini API key lives. Git-ignored by default. |
| `.streamlit/secrets.toml.example` | A safe template you commit instead, so anyone cloning the repo knows the expected format. |
| `.gitignore` | Guarantees `secrets.toml` (and any other real API key) never reaches GitHub. |

</details>

---

## 🔑 Where to Put Your Gemini API Key

1. Grab a free Gemini API key from **Google AI Studio**:
   👉 https://aistudio.google.com/apikey
2. Open `SPG/.streamlit/secrets.toml`
3. Replace the placeholder with your real key:

   ```toml
   GEMINI_API_KEY = "your-real-key-goes-here"
   ```

4. Save the file.

> ⚠️ **Never** paste your real key into any `.py` file, and never
> remove `secrets.toml` from `.gitignore`.

---

## 🖥️ Local Setup (Beginner-Friendly)

| Step | Command / Action |
|---|---|
| **1. Install Python** | Make sure Python 3.10+ is installed — check with `python --version` |
| **2. Get the project** | Place the entire `SPG/` folder on your computer |
| **3. Open a terminal** | `cd path/to/SPG` |
| **4. (Recommended) Create a virtual environment** | `python -m venv venv` then activate it — `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux) |
| **5. Install dependencies** | `pip install -r requirements.txt` |
| **6. Add your API key** | Edit `.streamlit/secrets.toml` as shown above |

---

## ▶️ Running the App

From inside the `SPG` folder, with your virtual environment activated:

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) —
open it in your browser and you're in! 🎉

---

## 🧪 Testing All Five Features

Try each of these example inputs to confirm everything works end to end:

| # | Feature | Example Input | What to Expect |
|---|---|---|---|
| 1 | Food–Medicine Interaction | Medicine: `Warfarin` · Food: `Grapefruit juice` | Explanation of the interaction, why it matters, and precautions |
| 2 | Missed Dose Guide | Medicine: `Metformin` · Situation: `Forgot afternoon dose, 3 hrs late` | General guidance + a clear warning against doubling doses |
| 3 | Alternative Options | Medicine: `Ibuprofen` · Reason: `Upsets my stomach` | Possible alternative categories + a safety note about consulting a professional |
| 4 | Storage & Handling | Medicine: `Insulin` | General storage guidance (e.g. refrigeration) + a disposal note |
| 5 | Quick Self-Assessment | Symptoms: `Mild headache and sore throat for 2 days, no fever` | General education, red flags, next steps — **no diagnosis** |

**Also test the safety pipeline:**

- ❓ Ask something unrelated, like *"Who won the cricket world cup?"* → SPG should politely refuse.
- 🚨 Type something like *"I think I'm having a severe allergic reaction and can't breathe"* → SPG should immediately show the red emergency banner.
- 🔌 Temporarily break your API key in `secrets.toml` → submitting a form should show a clear, friendly error instead of crashing.

---

## 🚀 GitHub Upload Guide

1. Initialize git inside the `SPG` folder (if not already done):
   ```bash
   git init
   ```
2. Confirm `.gitignore` is present (it already excludes `secrets.toml`).
3. Stage and commit everything:
   ```bash
   git add .
   git commit -m "Initial commit: SPG - Smart Pharma Guider"
   ```
4. Create a new **empty** repository on GitHub (don't initialize it with a README).
5. Link and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```
6. Double-check on GitHub.com that `.streamlit/secrets.toml` was **not** uploaded — only `secrets.toml.example` should be visible.

---

## ☁️ Streamlit Cloud Deployment Guide

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository and branch, and set the main file path to `app.py`.
4. Click **"Deploy"** — it's normal for the first launch to show an error, since no API key is configured yet.
5. Add your key (see below), then the app will restart automatically and work perfectly.

### 🔐 Exactly where to add `GEMINI_API_KEY` in Streamlit Cloud Secrets

1. On your deployed app's page, click the **"⋮"** menu → **"Settings"**.
2. Open the **"Secrets"** tab.
3. Paste:
   ```toml
   GEMINI_API_KEY = "your-real-key-goes-here"
   ```
4. Click **"Save"** — Streamlit Cloud restarts the app automatically with the key available as `st.secrets["GEMINI_API_KEY"]`.

---

## ✅ Final Deployment Checklist

- [ ] `secrets.toml` contains a real, working Gemini API key (locally)
- [ ] `secrets.toml` is **not** committed to GitHub (only `secrets.toml.example` is)
- [ ] `pip install -r requirements.txt` completes with no errors
- [ ] `streamlit run app.py` launches with no errors
- [ ] All five features return real, dynamic Gemini-generated answers
- [ ] Unrelated questions (e.g. cricket) are politely refused
- [ ] Emergency-style input triggers the red emergency banner
- [ ] Invalid/missing API key shows a friendly error, not a crash
- [ ] GitHub repository is pushed with secrets excluded
- [ ] Streamlit Cloud Secrets contain the real `GEMINI_API_KEY`
- [ ] Deployed app link works and behaves the same as local

---

## ⚠️ Disclaimer

SPG (Smart Pharma Guider) provides general, AI-generated educational
information about medicines. It is **not** a medical device, does
**not** diagnose conditions, and does **not** replace professional
medical or pharmacist advice.

**In a medical emergency, contact your local emergency number
immediately.**

<div align="center">

---

Built with 💚 using Python, Streamlit, and Google Gemini.

</div>