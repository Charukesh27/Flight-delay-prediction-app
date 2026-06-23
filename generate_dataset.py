"""
generate_dataset.py — Run ONCE to create flights.csv
Usage: python generate_dataset.py
"""
import pandas as pd, numpy as np, os, random

np.random.seed(42)
AIRLINES=["IndiGo","Air India","SpiceJet","Vistara","GoAir","AirAsia"]
AIRPORTS=["DEL","BOM","MAA","BLR","HYD","CCU","COK","GOI"]

rows=[]
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
        "airline":al,"origin":org,"dest":dst,"dep_hour":hr,"day_of_week":dow,
        "distance":dist,"delayed":int(random.random()<p)})

os.makedirs("data",exist_ok=True)
df=pd.DataFrame(rows)
df.to_csv("data/flights.csv",index=False)
print(f"✅ data/flights.csv — {len(df)} rows, {df['delayed'].sum()} delayed ({df['delayed'].mean()*100:.1f}%)")
print("Now run: python app.py")
