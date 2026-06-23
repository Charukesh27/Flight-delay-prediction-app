"""
database/db.py — SQLite layer for AeroVerse AI (with auth)
"""
import sqlite3, os, random, hashlib, secrets
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'aeroverse.db')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        passcode    TEXT NOT NULL,
        role        TEXT DEFAULT 'operator',
        created_at  TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS sessions (
        token       TEXT PRIMARY KEY,
        user_id     INTEGER,
        created_at  TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS predictions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        airline     TEXT, origin TEXT, dest TEXT,
        dep_hour    INTEGER, day_of_week INTEGER,
        distance    INTEGER, delayed INTEGER, probability REAL,
        created_at  TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        node_name   TEXT, event_type TEXT, message TEXT,
        severity    TEXT DEFAULT 'info',
        created_at  TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS security_events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        threat_type TEXT, source_ip TEXT, severity TEXT,
        description TEXT, status TEXT DEFAULT 'active',
        created_at  TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS ai_analytics (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name  TEXT, accuracy REAL, predictions INTEGER, anomalies INTEGER,
        created_at  TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit(); conn.close()
    _seed()

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ── AUTH ─────────────────────────────────────
def register_user(name, passcode):
    conn = get_conn()
    exists = conn.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone()
    if exists:
        conn.close(); return None, "Name already taken"
    conn.execute("INSERT INTO users(name,passcode) VALUES(?,?)", (name, _hash(passcode)))
    conn.commit(); conn.close()
    return True, "Registered successfully"

def login_user(name, passcode):
    conn = get_conn()
    u = conn.execute("SELECT * FROM users WHERE name=? AND passcode=?", (name, _hash(passcode))).fetchone()
    if not u:
        conn.close(); return None, "Invalid name or passcode"
    token = secrets.token_hex(32)
    conn.execute("INSERT INTO sessions(token,user_id) VALUES(?,?)", (token, u['id']))
    conn.commit(); conn.close()
    return token, dict(u)

def get_user_by_token(token):
    if not token: return None
    conn = get_conn()
    row = conn.execute("""
        SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id
        WHERE s.token=?
    """, (token,)).fetchone()
    conn.close()
    return dict(row) if row else None

def logout_token(token):
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit(); conn.close()

# ── PREDICTIONS ──────────────────────────────
def save_prediction(airline, origin, dest, dep_hour, dow, distance, delayed, prob):
    conn = get_conn()
    conn.execute("INSERT INTO predictions(airline,origin,dest,dep_hour,day_of_week,distance,delayed,probability) VALUES(?,?,?,?,?,?,?,?)",
        (airline, origin, dest, dep_hour, dow, distance, int(delayed), float(prob)))
    conn.commit(); conn.close()

def get_recent_predictions(limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── EVENTS ───────────────────────────────────
def save_event(node, etype, msg, severity='info'):
    conn = get_conn()
    conn.execute("INSERT INTO events(node_name,event_type,message,severity) VALUES(?,?,?,?)", (node,etype,msg,severity))
    conn.commit(); conn.close()

def get_recent_events(limit=30):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── SECURITY ─────────────────────────────────
def save_security_event(threat, ip, sev, desc):
    conn = get_conn()
    conn.execute("INSERT INTO security_events(threat_type,source_ip,severity,description) VALUES(?,?,?,?)", (threat,ip,sev,desc))
    conn.commit(); conn.close()

def get_security_events(limit=25):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_security_summary():
    conn = get_conn()
    t = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    a = conn.execute("SELECT COUNT(*) FROM security_events WHERE status='active'").fetchone()[0]
    cr= conn.execute("SELECT COUNT(*) FROM security_events WHERE severity='critical'").fetchone()[0]
    r = conn.execute("SELECT COUNT(*) FROM security_events WHERE status='resolved'").fetchone()[0]
    conn.close(); return {"total":t,"active":a,"critical":cr,"resolved":r}

def get_cyber_threats():
    conn = get_conn()
    rows = conn.execute("SELECT threat_type,COUNT(*) as count FROM security_events GROUP BY threat_type ORDER BY count DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── DASHBOARD ────────────────────────────────
def get_dashboard_summary():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] or 0
    delayed = conn.execute("SELECT COUNT(*) FROM predictions WHERE delayed=1").fetchone()[0] or 0
    avg_p = conn.execute("SELECT AVG(probability) FROM predictions").fetchone()[0] or 0
    events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] or 0
    conn.close()
    return {"total_predictions":total,"delayed":delayed,"on_time":total-delayed,
            "delay_rate":round((delayed/total*100) if total else 0,1),
            "avg_probability":round(avg_p*100,1),"total_events":events}

def get_delay_by_airline():
    conn = get_conn()
    rows = conn.execute("SELECT airline,COUNT(*) as total,SUM(delayed) as delayed,ROUND(AVG(probability)*100,1) as avg_prob FROM predictions GROUP BY airline ORDER BY total DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_delay_by_hour():
    conn = get_conn()
    rows = conn.execute("SELECT dep_hour as hour,COUNT(*) as total,SUM(delayed) as delayed,ROUND(AVG(probability)*100,1) as delay_pct FROM predictions GROUP BY dep_hour ORDER BY dep_hour").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_delay_by_day():
    DAYS=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    conn = get_conn()
    rows = conn.execute("SELECT day_of_week,COUNT(*) as total,SUM(delayed) as delayed FROM predictions GROUP BY day_of_week ORDER BY day_of_week").fetchall()
    conn.close()
    out=[]
    for r in rows:
        d=dict(r); d["day"]=DAYS[d["day_of_week"]]; out.append(d)
    return out

def get_delay_by_route():
    conn = get_conn()
    rows = conn.execute("SELECT origin||'→'||dest as route,COUNT(*) as total,SUM(delayed) as delayed,ROUND(AVG(probability)*100,1) as delay_pct FROM predictions GROUP BY route ORDER BY total DESC LIMIT 12").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_probability_distribution():
    conn = get_conn()
    rows = conn.execute("SELECT probability FROM predictions").fetchall()
    conn.close()
    b=[0]*10
    for r in rows:
        b[min(int(r["probability"]*10),9)]+=1
    return [{"range":f"{i*10}-{i*10+10}%","count":b[i]} for i in range(10)]

def get_network_event_pattern():
    conn = get_conn()
    rows = conn.execute("SELECT node_name,event_type,COUNT(*) as count FROM events GROUP BY node_name,event_type ORDER BY count DESC LIMIT 20").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_network_timeline():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 50").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_kpi_metrics():
    return {
        "runway_utilization": round(random.uniform(68,92),1),
        "gate_occupancy":     round(random.uniform(55,88),1),
        "on_time_performance":round(random.uniform(74,91),1),
        "fuel_efficiency":    round(random.uniform(82,95),1),
        "passenger_throughput":random.randint(2800,5200),
        "active_flights":     random.randint(18,42),
        "security_score":     round(random.uniform(85,99),1),
        "weather_impact":     random.choice(["Low","Moderate","High"]),
    }

def get_traffic_heatmap():
    return [{"hour":h,"day":d,"intensity":round(random.uniform(0.1,1.0),2)} for h in range(24) for d in range(7)]

def get_ai_analytics():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ai_analytics").fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── SEED ─────────────────────────────────────
def _seed():
    conn = get_conn(); c = conn.cursor()
    NODES=["ATC Tower","Runway Mgmt","Gate Control","Fleet Ops","Security","Weather Stn","Baggage","Catering","Emergency","Drone Patrol"]
    TYPES=["STATUS","ALERT","INFO","WARNING","HANDOFF"]
    MSGS=["Runway 09L cleared for landing","Gate B12 occupied","Weather advisory issued",
          "Baggage belt 3 operational","Fuel truck dispatched","Security sweep complete",
          "Flight pushed back","Emergency standby active","Catering loaded","Passenger bridge extended"]

    if c.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        rows=[]
        for _ in range(100):
            dt=(datetime.now()-timedelta(minutes=random.randint(1,1440))).isoformat(sep=" ",timespec="seconds")
            rows.append((random.choice(NODES),random.choice(TYPES),random.choice(MSGS),random.choice(["info","warning","critical","success"]),dt))
        c.executemany("INSERT INTO events(node_name,event_type,message,severity,created_at) VALUES(?,?,?,?,?)",rows)

    if c.execute("SELECT COUNT(*) FROM security_events").fetchone()[0] == 0:
        threats=["Port Scan","Brute Force","SQL Injection","DDoS","Phishing","Rogue Device","Data Exfil"]
        for _ in range(40):
            dt=(datetime.now()-timedelta(minutes=random.randint(1,2880))).isoformat(sep=" ",timespec="seconds")
            ip=f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
            sev=random.choice(["low","low","medium","medium","high","critical"])
            th=random.choice(threats)
            c.execute("INSERT INTO security_events(threat_type,source_ip,severity,description,status,created_at) VALUES(?,?,?,?,?,?)",
                (th,ip,sev,f"Detected {th} from {ip}",random.choice(["active","resolved","investigating"]),dt))

    if c.execute("SELECT COUNT(*) FROM ai_analytics").fetchone()[0] == 0:
        for m in ["DelayPredictor","AnomalyDetector","CongestionModel","GateOptimizer"]:
            c.execute("INSERT INTO ai_analytics(model_name,accuracy,predictions,anomalies) VALUES(?,?,?,?)",
                (m,round(random.uniform(0.78,0.97),3),random.randint(200,2000),random.randint(5,80)))

    conn.commit(); conn.close()
