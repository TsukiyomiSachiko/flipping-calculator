# OSRS Flipping Calculator - Complete Setup Guide

This guide will walk you through setting up both the **backend API** and the **frontend** from scratch.

## 📦 What You Need

### Required Software
1. **Python 3.8+** - For the backend API
   - Check: `python --version` or `python3 --version`
   - Download: https://www.python.org/downloads/

2. **Node.js 18+** - For the frontend
   - Check: `node --version`
   - Download: https://nodejs.org/

3. **Git** (optional) - For version control
   - Check: `git --version`
   - Download: https://git-scm.com/

## 🔧 Part 1: Backend API Setup

### Step 1: Set Up the Backend

```bash
# Navigate to the API directory
cd osrs-api

# Install Python dependencies
pip install -r requirements.txt

# (Optional) If you have an old CLI database, copy it to data/
# cp /path/to/old/osrs_flipping.db data/

# Start the API server
./run.sh
# OR
uvicorn app.main:app --reload
```

The API should now be running at `http://localhost:8000`

### Step 2: Verify the API is Running

Open your browser and go to:
```
http://localhost:8000/docs
```

You should see the interactive API documentation (Swagger UI).

### Step 3: Sync Items (First Time Only)

Option A - Using the API docs:
1. Go to `http://localhost:8000/docs`
2. Find `POST /api/items/sync`
3. Click "Try it out" → "Execute"
4. Wait 1-2 minutes for the sync to complete

Option B - Using curl:
```bash
curl -X POST http://localhost:8000/api/items/sync
```

This downloads all OSRS items from the Wiki API and stores them in your database.

## 🎨 Part 2: Frontend Setup

### Step 1: Install Dependencies

```bash
# Navigate to the frontend directory
cd osrs-flip-frontend

# Install all npm packages
npm install
```

This will install React, Vite, TanStack Query, Tailwind CSS, and all other dependencies.

### Step 2: Start the Development Server

```bash
npm run dev
```

You should see output like:
```
  VITE v6.0.3  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Step 3: Open the App

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the OSRS Flipping Calculator interface!

### Step 4: Sync Items in the UI (Optional)

If you didn't sync items via the API, you can do it from the UI:

1. Look for the **"🔄 Sync Items from OSRS Wiki"** button at the top
2. Click it and confirm
3. Wait for the sync to complete

## ✅ Verification Checklist

Check that everything is working:

- [ ] Backend API is running at `http://localhost:8000`
- [ ] API docs are accessible at `http://localhost:8000/docs`
- [ ] Items are synced (check via `GET /api/items` in docs)
- [ ] Frontend is running at `http://localhost:3000`
- [ ] You can see the navigation tabs (Find Flips, Portfolio, History)
- [ ] No console errors in the browser (F12 → Console)

## 🎯 First Usage

### 1. Find Your First Flip

1. Click on **"Find Flips"** tab
2. Set your available cash (e.g., "10M")
3. Set minimum profit (e.g., "100")
4. Click **"Search Flips"**
5. Browse the results!

### 2. Log a Purchase

1. Find an item you want to flip
2. Click the **"Buy"** button
3. Enter quantity and price
4. Click **"Confirm Buy"**

### 3. View Your Portfolio

1. Click on **"Portfolio"** tab
2. See your pending flips
3. See your total invested and expected profit

### 4. Complete a Flip

1. In the Portfolio tab, find your flip
2. Enter the sell price
3. Click **"Sell"**
4. Check the **"History"** tab to see your completed flip!

## 🔄 Daily Workflow

### Starting Your Session

1. **Start the backend:**
   ```bash
   cd osrs-api
   ./run.sh
   ```

2. **Start the frontend (in a new terminal):**
   ```bash
   cd osrs-flip-frontend
   npm run dev
   ```

3. **Open browser:**
   ```
   http://localhost:3000
   ```

### Stopping Your Session

1. Press `Ctrl+C` in both terminal windows to stop the servers
2. Your data is saved in the database automatically

## 🛠️ Troubleshooting

### Problem: "Cannot connect to API"

**Solution:**
1. Make sure the backend is running (`http://localhost:8000`)
2. Check if you can access `http://localhost:8000/docs`
3. Look at the terminal where the backend is running for errors

### Problem: "Port already in use"

**Solution for Backend (Port 8000):**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
# Or on Windows:
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

**Solution for Frontend (Port 3000):**
```bash
npx kill-port 3000
# Or run on different port:
npm run dev -- --port 3001
```

### Problem: "No items found"

**Solution:**
1. Make sure you synced items (Step 3 in Backend Setup)
2. Check the API logs for errors
3. Try syncing again from the UI

### Problem: "Module not found" errors

**Solution:**
```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend
rm -rf node_modules package-lock.json
npm install
```

### Problem: Browser shows blank page

**Solution:**
1. Open browser console (F12 → Console)
2. Look for error messages
3. Make sure backend is running
4. Try clearing browser cache (Ctrl+Shift+Delete)

## 📊 Understanding the Data Flow

```
Frontend (React)
    ↓ (HTTP Request)
Backend API (FastAPI)
    ↓ (Database Query)
SQLite Database
    ↓ (If needed)
OSRS Wiki API
```

When you search for flips:
1. Frontend sends filters to backend
2. Backend queries database for items
3. Backend fetches current prices from OSRS Wiki
4. Backend calculates profits and ROI
5. Backend returns results to frontend
6. Frontend displays them in a table

## 🎓 Next Steps

Now that you're set up:

1. **Customize filters** - Find flips that match your playstyle
2. **Track flips** - Log all your buys and sells
3. **Analyze history** - See which items are most profitable for you
4. **Experiment** - Try different items and strategies

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8000/docs`
- **Frontend README:** See `README.md` in the frontend folder
- **Backend README:** See `README.md` in the API folder
- **OSRS Wiki:** https://oldschool.runescape.wiki/

## 🆘 Still Having Issues?

If you're stuck:

1. Check all error messages carefully
2. Make sure all prerequisites are installed
3. Verify both servers are running
4. Check browser console for errors
5. Try restarting both servers

---

**Congratulations! You're ready to start flipping!** 🎉💰

Remember: The Grand Exchange is unpredictable. This tool helps you find opportunities, but always verify prices in-game before making trades.

Happy flipping! 🚀
