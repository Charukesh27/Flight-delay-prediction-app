# ✈ AeroVerse AI v3.0 — Smart Airport Digital Twin

> **Ultra-premium aviation intelligence platform** — login/register auth, AI delay prediction, live aircraft map, 15-node network simulation, cybersecurity center and real-time analytics.

---

## 🎨 Design Highlights
- **Cinematic dark** background with real Unsplash aviation photography on every page
- **Hero banners** with parallax-style zoom on every route (cockpit, runway, aircraft, cyber, ATC tower)
- **Space Grotesk + Outfit + Fira Code** professional typography
- **Glass-morphism cards** with cobalt/sky blue accents and gold highlights
- **Floating particle animations** on auth pages
- **Scan-line effect** across all pages

---

## 🔐 Auth System
- **Register** — name + passcode (SHA-256 hashed in SQLite)
- **Login** — name + passcode → secure HTTP-only cookie session
- **All pages protected** — redirect to `/login` if not authenticated
- **Logout** — clears session token from DB and cookie

---

## 📁 Project Structure

```
aeroverse2/
├── app.py                   ← Flask + SocketIO + auth middleware
├── generate_dataset.py      ← Run ONCE to create CSV
├── requirements.txt
├── data/
│   ├── flights.csv          ← Auto-generated training data
│   └── aeroverse.db         ← SQLite (auto-created on first run)
├── models/
│   ├── delay_model.pkl      ← Trained RF model
│   └── model_meta.json
├── ml/predictor.py          ← Random Forest (150 trees)
├── network/simulator.py     ← 15-node airport digital twin
├── database/db.py           ← Full SQLite layer + user auth
├── templates/
│   ├── base.html            ← Shared nav layout
│   ├── login.html           ← Login page (cockpit bg image)
│   ├── register.html        ← Register (runway bg image)
│   ├── index.html           ← Home (aerial bg)
│   ├── dashboard.html       ← Analytics (ATC bg)
│   ├── predict.html         ← Predictor (cockpit instrument bg)
│   ├── network.html         ← Network sim (radar bg)
│   ├── aircraft.html        ← Live map (sky bg)
│   └── security.html        ← Cyber center (dark server bg)
└── static/css/style.css     ← Full premium CSS
```

---

## ⚙️ Setup — Step by Step

### Step 1 — Copy project folder to your machine

### Step 2 — Create virtual environment
```bash
cd aeroverse2
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install packages
```bash
pip install -r requirements.txt
```

### Step 4 — Generate dataset (run ONCE)
```bash
python generate_dataset.py
```

### Step 5 — Start the app
```bash
python app.py
```
First run auto-creates the database and trains the ML model.

### Step 6 — Open browser
```
http://127.0.0.1:5000/login
```
→ Register a new account → Login → Explore all pages

---

## 🌐 Pages

| URL | Page | Background Image |
|---|---|---|
| `/login` | Login | Aerial night flight |
| `/register` | Register | Runway lights |
| `/` | Home | Aerial cityscape |
| `/dashboard` | Analytics | ATC overview |
| `/predict` | AI Predictor | Cockpit instruments |
| `/network` | Network Sim | Radar/satellite |
| `/aircraft` | Live Map | High altitude sky |
| `/security` | Cyber Center | Dark server room |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/login` | JSON login → sets cookie |
| POST | `/register` | JSON register |
| GET | `/logout` | Clears session |
| POST | `/predict` | AI delay prediction |
| POST | `/train` | Retrain ML model |
| GET | `/api/predictions` | Recent predictions |
| GET | `/api/model/stats` | Model accuracy |
| GET | `/api/dashboard/summary` | Summary KPIs |
| GET | `/api/dashboard/by-airline` | Airline delay stats |
| GET | `/api/dashboard/by-hour` | Hourly analysis |
| GET | `/api/dashboard/kpi` | Live KPIs |
| GET | `/api/aircraft/all` | Aircraft positions |
| GET | `/api/gates` | Gate occupancy |
| GET | `/api/runways` | Runway status |
| GET | `/api/weather` | Weather data |
| GET | `/api/security/events` | Security events |
| GET | `/api/security/summary` | Threat summary |
| POST | `/api/network/start` | Start simulation |
| POST | `/api/network/stop` | Stop simulation |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+ · Flask · Flask-SocketIO |
| Auth | SHA-256 passcode · HTTP-only cookie sessions · SQLite |
| ML | Scikit-learn RandomForest · 150 trees · 10 features |
| Database | SQLite (no external DB needed) |
| Frontend | Jinja2 · Chart.js 4 · Leaflet.js · Socket.IO client |
| Maps | Leaflet + CartoDB Dark tiles |
| Fonts | Space Grotesk · Outfit · Fira Code (Google Fonts) |
| Images | Unsplash free aviation photography |
| Design | Custom CSS glass-morphism · cobalt/gold · cinematic dark |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `data/flights.csv missing` | Run `python generate_dataset.py` |
| Port 5000 in use | Change `port=5000` in `app.py` |
| Login cookie not working | Use `http://` not file:// in browser |
| Map not loading | Check internet (Leaflet CDN + Unsplash images) |

---

*AeroVerse AI v3.0 — Built for PG final year project / research / portfolio*
"# Flight-delay-prediction-app" 
