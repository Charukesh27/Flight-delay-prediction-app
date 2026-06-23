"""network/simulator.py — Airport Digital Twin Engine"""
import threading, time, random
from datetime import datetime

_running=False; _thread=None; _socketio=None

AIRLINES=["IndiGo","Air India","SpiceJet","Vistara","GoAir","AirAsia"]
AIRPORTS=["DEL","BOM","MAA","BLR","HYD","CCU","COK","GOI"]
AIRPORT_POS={"DEL":(28.56,77.10),"BOM":(19.09,72.87),"MAA":(12.99,80.17),
             "BLR":(13.20,77.71),"HYD":(17.24,78.43),"CCU":(22.65,88.45),
             "COK":(10.16,76.39),"GOI":(15.38,73.83)}

NODES=[
    {"id":1, "name":"ATC Tower",         "type":"control",    "port":9001},
    {"id":2, "name":"Runway Management", "type":"runway",     "port":9002},
    {"id":3, "name":"Gate Control",      "type":"gate",       "port":9003},
    {"id":4, "name":"Aircraft Fleet",    "type":"fleet",      "port":9004},
    {"id":5, "name":"Fuel Services",     "type":"ground",     "port":9005},
    {"id":6, "name":"Baggage Handling",  "type":"ground",     "port":9006},
    {"id":7, "name":"Catering Services", "type":"ground",     "port":9007},
    {"id":8, "name":"Security Ops",      "type":"security",   "port":9008},
    {"id":9, "name":"Immigration",       "type":"security",   "port":9009},
    {"id":10,"name":"Weather Station",   "type":"weather",    "port":9010},
    {"id":11,"name":"Maintenance",       "type":"maintenance","port":9011},
    {"id":12,"name":"Emergency Team",    "type":"emergency",  "port":9012},
    {"id":13,"name":"Passenger Buses",   "type":"ground",     "port":9013},
    {"id":14,"name":"Smart Parking",     "type":"utility",    "port":9014},
    {"id":15,"name":"Drone Patrol",      "type":"security",   "port":9015},
]

GATES=[{"id":f"G{i}","terminal":f"T{(i-1)//8+1}","status":"free","aircraft":None,"flight":None} for i in range(1,33)]

RUNWAYS=[
    {"id":"RWY-09L","name":"Runway 09L","length_m":3900,"status":"active","landing_queue":0,"takeoff_queue":0},
    {"id":"RWY-09R","name":"Runway 09R","length_m":4200,"status":"active","landing_queue":0,"takeoff_queue":0},
    {"id":"RWY-27L","name":"Runway 27L","length_m":3600,"status":"maintenance","landing_queue":0,"takeoff_queue":0},
    {"id":"RWY-27R","name":"Runway 27R","length_m":4000,"status":"active","landing_queue":0,"takeoff_queue":0},
]

_aircraft=[]; _events=[]; _security=[]; _weather={}
_node_status={n["id"]:{"status":"online","load":30,"messages":0} for n in NODES}

EVTS=[
    ("ATC cleared runway {rwy} for landing approach","info"),
    ("Gate {gate} assigned to flight {flt}","info"),
    ("Weather advisory: wind shear on approach","warning"),
    ("Baggage carousel {num} now operational","success"),
    ("EMERGENCY: medical team to gate {gate}","critical"),
    ("Fuel truck dispatched to apron {num}","info"),
    ("Security sweep complete — all clear","success"),
    ("Catering vehicle en-route to {flt}","info"),
    ("Immigration queue at {pct}% capacity","warning"),
    ("ATC HANDOFF: {flt} to approach control","info"),
    ("Runway {rwy} inspected — clear","success"),
    ("Drone patrol sector {num} complete","info"),
    ("Smart parking lot C at {pct}%","info"),
    ("Maintenance scheduled on RWY-27L","info"),
    ("Passenger bus dispatched to remote stand","info"),
]

THREATS=["Port Scan","Brute Force","SQL Injection","DDoS","Rogue Device","Data Exfil","Phishing"]
SIGS=["Multiple failed auth attempts","Unusual data transfer volume","Unknown device on ATC subnet",
      "ARP poisoning attempt","C2 beacon detected","Encrypted tunnel to unknown host"]

def _init_aircraft():
    global _aircraft; _aircraft=[]
    for i in range(22):
        org=random.choice(AIRPORTS); dst=random.choice([a for a in AIRPORTS if a!=org])
        op=AIRPORT_POS[org]; dp=AIRPORT_POS[dst]; t=random.uniform(0,1)
        al=random.choice(AIRLINES)
        _aircraft.append({"id":i+1,
            "flight_num":f"{al[:2].upper()}{random.randint(100,999)}","airline":al,
            "origin":org,"dest":dst,
            "lat":round(op[0]+(dp[0]-op[0])*t+random.uniform(-0.1,0.1),4),
            "lon":round(op[1]+(dp[1]-op[1])*t+random.uniform(-0.1,0.1),4),
            "altitude":random.randint(8000,38000),"speed":random.randint(420,890),
            "heading":random.randint(0,359),
            "status":random.choice(["Cruising","Climbing","Descending","Approach","Taxi","Boarding"]),
            "gate":f"G{random.randint(1,32)}","progress":round(t,3),
            "_op":list(op),"_dp":list(dp)})

def _init_weather():
    global _weather
    _weather={"condition":random.choice(["Clear","Partly Cloudy","Overcast","Light Rain","Thunderstorm","Fog","Windy"]),
        "temp_c":round(random.uniform(18,38),1),"wind_kph":round(random.uniform(8,55),1),
        "wind_dir":random.choice(["N","NE","E","SE","S","SW","W","NW"]),
        "visibility_km":round(random.uniform(2,12),1),"humidity":random.randint(35,92),
        "pressure":round(random.uniform(1000,1025),1),"ceiling_ft":random.randint(1500,30000),
        "impact":random.choice(["None","Minor Delays","Moderate Delays","Major Delays"]),
        "updated":datetime.now().isoformat()}

_init_aircraft(); _init_weather()

def move_aircraft_step():
    for ac in _aircraft:
        ac["progress"]=min(1.0,ac["progress"]+random.uniform(0.003,0.012))
        op=ac["_op"]; dp=ac["_dp"]; t=ac["progress"]
        ac["lat"]=round(op[0]+(dp[0]-op[0])*t+random.uniform(-0.05,0.05),4)
        ac["lon"]=round(op[1]+(dp[1]-op[1])*t+random.uniform(-0.05,0.05),4)
        ac["status"]="Climbing" if t<0.1 else "Cruising" if t<0.85 else "Descending" if t<0.95 else "Approach"
        if ac["progress"]>=1.0:
            no=ac["dest"]; nd=random.choice([a for a in AIRPORTS if a!=no])
            al=random.choice(AIRLINES)
            ac.update({"origin":no,"dest":nd,"progress":0.0,"_op":list(AIRPORT_POS[no]),"_dp":list(AIRPORT_POS[nd]),
                       "airline":al,"flight_num":f"{al[:2].upper()}{random.randint(100,999)}",
                       "altitude":random.randint(8000,38000),"speed":random.randint(420,890)})

def _gen_event():
    node=random.choice(NODES)
    tmpl,sev=random.choice(EVTS)
    msg=tmpl.format(rwy=random.choice(["09L","09R","27R"]),
        gate=f"G{random.randint(1,32)}",
        flt=f"{random.choice(AIRLINES)[:2].upper()}{random.randint(100,999)}",
        num=random.randint(1,8),pct=random.randint(40,95))
    ev={"node_name":node["name"],"event_type":random.choice(["STATUS","ALERT","INFO","HANDOFF","WARNING"]),
        "message":msg,"severity":sev,
        "created_at":datetime.now().isoformat(sep=" ",timespec="seconds")}
    _events.insert(0,ev)
    if len(_events)>200: _events.pop()
    try:
        from database.db import save_event
        save_event(ev["node_name"],ev["event_type"],ev["message"],ev["severity"])
    except: pass

def _gen_security():
    th=random.choice(THREATS); sig=random.choice(SIGS)
    ip=f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    sev=random.choice(["low","low","medium","medium","high","critical"])
    ev={"threat_type":th,"source_ip":ip,"severity":sev,"description":f"{sig} — {ip}",
        "status":"active","created_at":datetime.now().isoformat(sep=" ",timespec="seconds")}
    _security.insert(0,ev)
    if len(_security)>100: _security.pop()

def _loop():
    cycle=0
    while _running:
        time.sleep(2); cycle+=1
        move_aircraft_step(); _gen_event()
        if cycle%8==0: _gen_security()
        if cycle%15==0: _init_weather()
        for nid in _node_status:
            _node_status[nid]["load"]=random.randint(20,95)
            _node_status[nid]["messages"]+=random.randint(1,5)
        for rwy in RUNWAYS:
            if rwy["status"]=="active":
                rwy["landing_queue"]=random.randint(0,5); rwy["takeoff_queue"]=random.randint(0,4)
        if _socketio:
            try:
                _socketio.emit("sim_event",_events[0] if _events else {})
                if cycle%5==0: _socketio.emit("aircraft_update",{"aircraft":_aircraft[:22]})
            except: pass

def start_network_simulation(sio=None):
    global _running,_thread,_socketio
    _socketio=sio
    if not _running:
        _running=True
        _thread=threading.Thread(target=_loop,daemon=True); _thread.start()

def stop_network_simulation():
    global _running; _running=False

def get_network_status():
    return {"running":_running,
            "nodes":[{**n,"status":_node_status[n["id"]]["status"],
                      "load":_node_status[n["id"]]["load"],
                      "messages":_node_status[n["id"]]["messages"]} for n in NODES],
            "total_events":len(_events)}

def get_all_aircraft(): return _aircraft
def get_gate_status():
    for i,g in enumerate(GATES):
        g["status"]=random.choice(["occupied","occupied","free","boarding"]) if i<14 else random.choice(["free","free","occupied"])
        if g["status"]!="free":
            al=random.choice(AIRLINES); g["flight"]=f"{al[:2].upper()}{random.randint(100,999)}"
    return GATES
def get_runway_status(): return RUNWAYS
def get_weather_data(): return _weather
def get_security_events(limit=25): return _security[:limit]
def get_cyber_threats():
    c={}
    for e in _security: c[e["threat_type"]]=c.get(e["threat_type"],0)+1
    return [{"threat":k,"count":v} for k,v in sorted(c.items(),key=lambda x:-x[1])]
def get_node_metrics():
    return [{**n,"status":_node_status[n["id"]]["status"],"load":_node_status[n["id"]]["load"],
             "messages":_node_status[n["id"]]["messages"]} for n in NODES]
def assign_gate(fid,pref=None):
    for g in GATES:
        if g["status"]=="free":
            g["status"]="occupied"; g["flight"]=fid
            return {"success":True,"gate":g["id"],"terminal":g["terminal"]}
    return {"success":False,"message":"No free gates"}
def get_fleet_utilization():
    return {"total":len(_aircraft),
            "cruising":sum(1 for a in _aircraft if a["status"]=="Cruising"),
            "approach":sum(1 for a in _aircraft if a["status"] in ["Approach","Descending"]),
            "ground":sum(1 for a in _aircraft if a["status"] in ["Taxi","Boarding"]),
            "airlines":{al:sum(1 for a in _aircraft if a["airline"]==al) for al in AIRLINES}}
