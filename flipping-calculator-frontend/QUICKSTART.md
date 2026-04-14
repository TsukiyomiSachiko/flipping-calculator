# Quick Start Guide

Get up and running in 3 steps!

## Prerequisites Check

```bash
# Check Python (need 3.8+)
python --version

# Check Node.js (need 18+)
node --version
```

Don't have them? Download:
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

## Step 1: Start Backend API

```bash
cd osrs-api
pip install -r requirements.txt
./run.sh
```

Keep this terminal open. API runs at `http://localhost:8000`

## Step 2: Start Frontend (New Terminal)

```bash
cd osrs-flip-frontend
npm install
npm run dev
```

Keep this terminal open. Frontend runs at `http://localhost:3000`

## Step 3: Open Browser

Go to: `http://localhost:3000`

Click "🔄 Sync Items" button (first time only, takes 1-2 min)

## You're Done! 🎉

- **Find Flips** - Search profitable items
- **Portfolio** - Track your flips
- **History** - View completed flips

---

**Need detailed help?** See `SETUP_GUIDE.md`

**Having issues?** Make sure both terminals are still running!
