"""ml/predictor.py — Flight Delay Prediction"""
import os, json, random
import numpy as np
import joblib
from datetime import datetime

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'delay_model.pkl')
META_PATH  = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_meta.json')

AIRLINES = ["IndiGo","Air India","SpiceJet","Vistara","GoAir","AirAsia"]
AIRPORTS = ["DEL","BOM","MAA","BLR","HYD","CCU","COK","GOI"]

_model = None
_meta  = {}

def _feats(data):
    al  = AIRLINES.index(data.get("airline","IndiGo")) if data.get("airline") in AIRLINES else 0
    org = AIRPORTS.index(data.get("origin","DEL"))     if data.get("origin")  in AIRPORTS else 0
    dst = AIRPORTS.index(data.get("dest","BOM"))       if data.get("dest")    in AIRPORTS else 1
    hr  = int(data.get("dep_hour",8))
    dow = int(data.get("day_of_week",1))
    dist= int(data.get("distance",1200))
    return [al,org,dst,hr,dow,dist,
            1 if hr in range(6,10) or hr in range(17,21) else 0,
            1 if dow>=4 else 0,
            1 if data.get("airline") in ["GoAir","SpiceJet","AirAsia"] else 0,
            1 if dist>1500 else 0]

def train_model():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    import pandas as pd

    csv = os.path.join(os.path.dirname(__file__),'..','data','flights.csv')
    if not os.path.exists(csv): _gen(csv)

    df = pd.read_csv(csv)
    X  = np.array([_feats(r) for _,r in df.iterrows()])
    y  = df["delayed"].values
    Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42)

    clf = RandomForestClassifier(n_estimators=150, max_depth=9, random_state=42)
    clf.fit(Xtr,ytr)
    acc = accuracy_score(yte, clf.predict(Xte))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    meta = {"accuracy":round(float(acc),4),"trained_at":datetime.now().isoformat(),
            "n_samples":len(df),"model_type":"RandomForestClassifier",
            "delay_rate":round(float(df["delayed"].mean()),4)}
    with open(META_PATH,"w") as f: json.dump(meta,f)

    global _model,_meta
    _model=clf; _meta=meta
    return f"Trained — Accuracy: {acc*100:.1f}% on {len(df)} samples"

def _load():
    global _model,_meta
    if _model is None:
        if os.path.exists(MODEL_PATH): _model=joblib.load(MODEL_PATH)
        else: train_model()
    if not _meta and os.path.exists(META_PATH):
        with open(META_PATH) as f: _meta=json.load(f)

def predict_delay(data):
    from database.db import save_prediction
    _load()
    f=_feats(data); X=np.array([f])
    prob=float(_model.predict_proba(X)[0][1])
    delayed=prob>=0.5
    DAYS=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    tips=[]
    if f[6]: tips.append("Peak-hour departure increases risk")
    if f[7]: tips.append("Weekend traffic creates congestion")
    if f[8]: tips.append("Carrier has above-average delay history")
    if f[9]: tips.append("Long-haul route more delay-prone")

    save_prediction(data.get("airline","IndiGo"),data.get("origin","DEL"),data.get("dest","BOM"),
        int(data.get("dep_hour",8)),int(data.get("day_of_week",1)),int(data.get("distance",1200)),delayed,prob)

    return {
        "airline":data.get("airline"),"route":f"{data.get('origin')} → {data.get('dest')}",
        "flight_date":DAYS[int(data.get("day_of_week",1))],
        "dep_hour":f"{int(data.get('dep_hour',8)):02d}:00",
        "distance":data.get("distance"),
        "probability":round(prob,4),"delayed":delayed,
        "label":"⚠ DELAYED" if delayed else "✅ ON TIME",
        "risk_level":"HIGH" if prob>0.7 else "MEDIUM" if prob>0.4 else "LOW",
        "confidence":round(max(prob,1-prob)*100,1),
        "tips":tips,"model_acc":round(_meta.get("accuracy",0)*100,1),
    }

def get_model_stats():
    _load()
    return {"accuracy":round(_meta.get("accuracy",0)*100,1),
            "trained_at":_meta.get("trained_at","—"),
            "n_samples":_meta.get("n_samples",0),
            "model_type":_meta.get("model_type","RandomForest"),
            "delay_rate":round(_meta.get("delay_rate",0)*100,1),
            "features":["Airline","Origin","Dest","Dep Hour","Day","Distance","Peak","Weekend","LCC","Long-Haul"]}

def _gen(csv):
    import pandas as pd
    np.random.seed(42); rows=[]
    for _ in range(1200):
        al=random.choice(AIRLINES); org=random.choice(AIRPORTS)
        dst=random.choice([a for a in AIRPORTS if a!=org])
        hr=random.randint(5,23); dow=random.randint(0,6); dist=random.randint(300,2500)
        p=0.10
        if hr in range(6,10) or hr in range(17,21): p+=0.20
        if dow>=4: p+=0.12
        if al in ["GoAir","SpiceJet"]: p+=0.15
        if dist>1500: p+=0.08
        p+=random.uniform(-0.05,0.10); p=float(np.clip(p,0.05,0.95))
        rows.append({"flight_num":f"{al[:2].upper()}{random.randint(100,999)}",
            "airline":al,"origin":org,"dest":dst,"dep_hour":hr,"day_of_week":dow,"distance":dist,"delayed":int(random.random()<p)})
    os.makedirs(os.path.dirname(csv),exist_ok=True)
    pd.DataFrame(rows).to_csv(csv,index=False)
