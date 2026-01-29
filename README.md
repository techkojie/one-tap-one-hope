# 1 TAP = 1 HOPE

A Telegram Mini App that lets users help children in Africa with **one single tap**.  
No payment required from users — real impact is funded by sponsors (fiat + crypto).  
Every verified tap is recorded and matched to sponsor pledges.

## Project Status (as of January 2026)

- **Frontend**: Pure HTML + CSS + vanilla JS (no React, no build step)
- **Backend**: Flask + aiogram (Telegram bot) + SQLite
- **Goal**: One tap → record in DB → show success message (currently local)
- **Next**: Stabilize bot polling → host frontend on Vercel → connect tap to backend → add sponsor payments

## Folder Structure
tap-help/
├── index.html         ← Main mini-app page
├── style.css          ← Simple, mobile-friendly styles
├── script.js          ← Tap logic + fetch to Flask backend
├── backend/
│   ├── app.py         ← Flask server + Telegram bot + DB logic
│   ├── .env           ← Secrets (TELEGRAM_BOT_TOKEN, etc.) — never commit!
│   ├── requirements.txt
│   └── hope.db        ← SQLite database (gitignored)
└── README.md

## How to Run Locally

### 1. Backend (Flask + Bot)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
→ Runs on http://localhost:5000
→ Bot should respond to /start (if token is valid)
2. Frontend (static files)
Just open index.html in any browser (double-click the file).
Or serve it locally with Python (recommended for CORS-free testing):
# In the root folder (where index.html is)
python -m http.server 8000

→ Open http://localhost:8000 in browser
3. Test the Tap Flow

Make sure Flask is running
Open http://localhost:8000 (or double-click index.html)
Click TAP TO HELP
After 3–5 seconds delay → should show success message if backend is reachable
Check hope.db (use SQLite viewer) → new row in taps table

4. Connect to Telegram Mini App

Host the frontend on Vercel (see below)
In @BotFather → your bot → Edit Bot → Edit Menu Button → Web App
Paste your Vercel URL (e.g. https://your-app-name.vercel.app)
Save
Open bot → tap menu → open app → tap button → watch DB

Hosting the Frontend (Vercel – Recommended)

Push the repo to GitHub (only index.html, style.css, script.js, backend/ folder)
Go to https://vercel.com → New Project → Import Git Repository
Settings:
Framework Preset: Other (static files)
Root Directory: leave blank
Build & Output: leave blank

Deploy → get live URL in ~30 seconds
Update script.js fetch URL later to your hosted backend

Future Roadmap

Stabilize Telegram bot polling (fix token / retry loop)
Host backend (Render / Railway / Fly.io)
Add sponsor form + payment buttons (Stripe / Paystack / TON)
Show real impact stats
Public transparency dashboard

License
MIT – free to use for good causes.
Made with ❤️ in Lagos for African children.
@ose_jay1
text
