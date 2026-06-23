"""AeroVerse AI v3.0 — Main Flask App with Auth"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from flask_socketio import SocketIO, emit
import threading, time
from datetime import datetime
from functools import wraps

from ml.predictor import predict_delay, train_model, get_model_stats
from network.simulator import (start_network_simulation, stop_network_simulation,
    get_network_status, get_all_aircraft, get_gate_status, get_runway_status,
    get_weather_data, get_security_events, get_node_metrics, get_cyber_threats,
    move_aircraft_step, assign_gate, get_fleet_utilization)
from database.db import (init_db, get_recent_predictions, get_recent_events,
    get_dashboard_summary, get_delay_by_airline, get_delay_by_hour, get_delay_by_day,
    get_delay_by_route, get_probability_distribution, get_network_event_pattern,
    get_network_timeline, get_security_summary, get_kpi_metrics, get_traffic_heatmap,
    get_ai_analytics, get_cyber_threats as db_cyber,
    register_user, login_user, get_user_by_token, logout_token)

app = Flask(__name__)
app.config["SECRET_KEY"] = "aeroverse-ultra-secret-2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── AUTH DECORATOR ───────────────────────────
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("av_token")
        user  = get_user_by_token(token)
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"error":"Unauthorized"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    return get_user_by_token(request.cookies.get("av_token"))

# ── AUTH PAGES ───────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        d = request.get_json(force=True)
        token, result = login_user(d.get("name",""), d.get("passcode",""))
        if token:
            resp = jsonify({"ok":True,"name":result["name"],"role":result["role"]})
            resp.set_cookie("av_token", token, max_age=86400*7, httponly=True, samesite="Lax")
            return resp
        return jsonify({"ok":False,"error":result}), 401
    # Already logged in?
    if get_current_user():
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register_page():
    if request.method == "POST":
        d = request.get_json(force=True)
        ok, msg = register_user(d.get("name","").strip(), d.get("passcode",""))
        if ok:
            return jsonify({"ok":True,"message":msg})
        return jsonify({"ok":False,"error":msg}), 400
    if get_current_user():
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    token = request.cookies.get("av_token")
    if token: logout_token(token)
    resp = make_response(redirect(url_for("login_page")))
    resp.delete_cookie("av_token")
    return resp

# ── PROTECTED PAGES ──────────────────────────
@app.route("/")
@require_auth
def home():
    return render_template("index.html", user=get_current_user())

@app.route("/dashboard")
@require_auth
def dashboard():
    return render_template("dashboard.html", user=get_current_user())

@app.route("/predict", methods=["GET","POST"])
@require_auth
def predict():
    if request.method == "POST":
        return jsonify(predict_delay(request.get_json(force=True)))
    return render_template("predict.html", user=get_current_user())

@app.route("/network")
@require_auth
def network():
    return render_template("network.html", user=get_current_user())

@app.route("/aircraft")
@require_auth
def aircraft():
    return render_template("aircraft.html", user=get_current_user())

@app.route("/security")
@require_auth
def security():
    return render_template("security.html", user=get_current_user())

# ── PREDICTION APIs ───────────────────────────
@app.route("/api/predictions")
@require_auth
def api_predictions(): return jsonify(get_recent_predictions(20))

@app.route("/api/model/stats")
@require_auth
def api_model_stats(): return jsonify(get_model_stats())

@app.route("/train", methods=["POST"])
@require_auth
def train(): return jsonify({"message": train_model()})

# ── NETWORK APIs ──────────────────────────────
@app.route("/api/network/start", methods=["POST"])
@require_auth
def start_net():
    start_network_simulation(socketio)
    return jsonify({"status":"running"})

@app.route("/api/network/stop", methods=["POST"])
@require_auth
def stop_net():
    stop_network_simulation()
    return jsonify({"status":"stopped"})

@app.route("/api/network/status")
@require_auth
def net_status(): return jsonify(get_network_status())

@app.route("/api/network/events")
@require_auth
def net_events(): return jsonify(get_recent_events(30))

@app.route("/api/network/nodes")
@require_auth
def net_nodes(): return jsonify(get_node_metrics())

# ── AIRCRAFT APIs ─────────────────────────────
@app.route("/api/aircraft/all")
@require_auth
def api_aircraft(): return jsonify(get_all_aircraft())

@app.route("/api/aircraft/fleet-utilization")
@require_auth
def api_fleet(): return jsonify(get_fleet_utilization())

@app.route("/api/gates")
@require_auth
def api_gates(): return jsonify(get_gate_status())

@app.route("/api/runways")
@require_auth
def api_runways(): return jsonify(get_runway_status())

# ── WEATHER/SECURITY APIs ─────────────────────
@app.route("/api/weather")
@require_auth
def api_weather(): return jsonify(get_weather_data())

@app.route("/api/security/events")
@require_auth
def api_sec_events(): return jsonify(get_security_events(25))

@app.route("/api/security/threats")
@require_auth
def api_threats(): return jsonify(get_cyber_threats())

@app.route("/api/security/summary")
@require_auth
def api_sec_sum(): return jsonify(get_security_summary())

# ── DASHBOARD APIs ────────────────────────────
@app.route("/api/dashboard/summary")
@require_auth
def api_summary(): return jsonify(get_dashboard_summary())

@app.route("/api/dashboard/by-airline")
@require_auth
def api_airline(): return jsonify(get_delay_by_airline())

@app.route("/api/dashboard/by-hour")
@require_auth
def api_hour(): return jsonify(get_delay_by_hour())

@app.route("/api/dashboard/by-day")
@require_auth
def api_day(): return jsonify(get_delay_by_day())

@app.route("/api/dashboard/by-route")
@require_auth
def api_route(): return jsonify(get_delay_by_route())

@app.route("/api/dashboard/probability-dist")
@require_auth
def api_prob(): return jsonify(get_probability_distribution())

@app.route("/api/dashboard/kpi")
@require_auth
def api_kpi(): return jsonify(get_kpi_metrics())

@app.route("/api/dashboard/ai-analytics")
@require_auth
def api_ai(): return jsonify(get_ai_analytics())

# ── WEBSOCKET ─────────────────────────────────
@socketio.on("connect")
def on_connect():
    emit("connected", {"msg":"AeroVerse AI connected"})

def _push_loop():
    while True:
        time.sleep(4)
        try:
            move_aircraft_step()
            socketio.emit("live_update", {
                "aircraft": get_all_aircraft()[:20],
                "weather":  get_weather_data(),
                "ts":       datetime.now().isoformat()
            })
        except: pass

if __name__ == "__main__":
    init_db()
    train_model()
    threading.Thread(target=_push_loop, daemon=True).start()
    print("\n✈  AeroVerse AI v3.0 — Smart Airport Digital Twin")
    print("─"*52)
    print("  Login     → http://127.0.0.1:5000/login")
    print("  Register  → http://127.0.0.1:5000/register")
    print("  Home      → http://127.0.0.1:5000/")
    print("  Dashboard → http://127.0.0.1:5000/dashboard")
    print("─"*52+"\n")
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
