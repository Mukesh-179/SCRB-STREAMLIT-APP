"""
backend.py — SCRB Crime Intelligence Platform
Pure-Python analytics engine. No UI code here; Streamlit (app.py) imports this.
"""
import pandas as pd
import numpy as np
import re, random
from functools import lru_cache
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

random.seed(42)
np.random.seed(42)

DATA_PATH = "Crime_Data.csv"

DISTRICTS = {
    "Bengaluru Urban": (12.9716, 77.5946, 1.0), "Bengaluru Rural": (13.2846, 77.5808, 0.32),
    "Mysuru": (12.2958, 76.6394, 0.55), "Belagavi": (15.8497, 74.4977, 0.5),
    "Ballari": (15.1394, 76.9214, 0.42), "Tumakuru": (13.3379, 77.1173, 0.4),
    "Kalaburagi": (17.3297, 76.8343, 0.44), "Dakshina Kannada": (12.9141, 74.8560, 0.48),
    "Shivamogga": (13.9299, 75.5681, 0.36), "Hubballi-Dharwad": (15.3647, 75.1240, 0.5),
    "Vijayapura": (16.8302, 75.7100, 0.34), "Davanagere": (14.4644, 75.9218, 0.38),
    "Raichur": (16.2076, 77.3463, 0.33), "Bidar": (17.9133, 77.5301, 0.3),
    "Hassan": (13.0072, 76.0964, 0.3), "Mandya": (12.5242, 76.8958, 0.3),
    "Udupi": (13.3409, 74.7421, 0.32), "Chikkamagaluru": (13.3161, 75.7720, 0.25),
    "Kolar": (13.1362, 78.1298, 0.3), "Chikkaballapur": (13.4355, 77.7315, 0.26),
    "Koppal": (15.3547, 76.1548, 0.26), "Gadag": (15.4315, 75.6298, 0.24),
    "Haveri": (14.7936, 75.4044, 0.26), "Uttara Kannada": (14.7951, 74.6982, 0.28),
    "Chitradurga": (14.2296, 76.3985, 0.28), "Chamarajanagar": (11.9236, 76.9456, 0.22),
    "Kodagu": (12.4244, 75.7382, 0.2), "Yadgir": (16.7683, 77.1376, 0.22),
    "Ramanagara": (12.7159, 77.2810, 0.28), "Vijayanagara": (15.2350, 76.4600, 0.25),
}
POP_LAKH = {
    "Bengaluru Urban": 96.2, "Bengaluru Rural": 15.1, "Mysuru": 30.9, "Belagavi": 47.8,
    "Ballari": 27.5, "Tumakuru": 27.0, "Kalaburagi": 25.7, "Dakshina Kannada": 21.8,
    "Shivamogga": 17.5, "Hubballi-Dharwad": 18.5, "Vijayapura": 21.8, "Davanagere": 19.5,
    "Raichur": 19.3, "Bidar": 17.0, "Hassan": 17.6, "Mandya": 18.1, "Udupi": 11.8,
    "Chikkamagaluru": 11.4, "Kolar": 15.4, "Chikkaballapur": 12.5, "Koppal": 13.9,
    "Gadag": 10.6, "Haveri": 16.0, "Uttara Kannada": 14.5, "Chitradurga": 16.6,
    "Chamarajanagar": 10.3, "Kodagu": 5.5, "Yadgir": 11.7, "Ramanagara": 10.8, "Vijayanagara": 14.3,
}
URBAN_PCT = {
    "Bengaluru Urban": 91, "Bengaluru Rural": 34, "Mysuru": 42, "Belagavi": 26,
    "Ballari": 40, "Tumakuru": 22, "Kalaburagi": 32, "Dakshina Kannada": 46,
    "Shivamogga": 30, "Hubballi-Dharwad": 58, "Vijayapura": 25, "Davanagere": 38,
    "Raichur": 24, "Bidar": 23, "Hassan": 18, "Mandya": 17, "Udupi": 33,
    "Chikkamagaluru": 19, "Kolar": 21, "Chikkaballapur": 16, "Koppal": 20, "Gadag": 28,
    "Haveri": 17, "Uttara Kannada": 27, "Chitradurga": 22, "Chamarajanagar": 15,
    "Kodagu": 22, "Yadgir": 15, "Ramanagara": 20, "Vijayanagara": 24,
}
LITERACY_PCT = {  # synthetic, for socio-economic overlay (feature 8)
    d: round(min(95, max(58, URBAN_PCT[d]*0.55 + 45 + np.random.normal(0, 3))), 1) for d in DISTRICTS
}
DIST_NAMES = list(DISTRICTS.keys())


def _clean(s):
    if pd.isna(s):
        return s
    return re.sub(r"\s+", " ", str(s)).strip()


@lru_cache(maxsize=1)
def load_raw():
    df = pd.read_csv(DATA_PATH)
    for c in ["Major Crime Head", "Crime Head and Section", "Minor Crime Head"]:
        df[c] = df[c].apply(_clean)
    df["Commits"] = df["Commits"].fillna(0).astype(float)
    df["MonthDate"] = pd.to_datetime(df["Month"], format="%b-%y")
    df = df.sort_values("MonthDate")
    return df


def month_labels(df):
    months = sorted(df["MonthDate"].unique())
    return months, [pd.Timestamp(m).strftime("%b-%y") for m in months]


# ---------------------------------------------------------------- FEATURE 1
def monthly_totals(df):
    months, labels = month_labels(df)
    s = df.groupby("MonthDate")["Commits"].sum().reindex(months).fillna(0)
    return pd.DataFrame({"month": labels, "total": s.values})


# ---------------------------------------------------------------- FEATURE 2
def top_categories(df, n=15):
    s = df.groupby("Major Crime Head")["Commits"].sum().sort_values(ascending=False)
    return s.head(n)


def category_monthly(df, cats):
    months, labels = month_labels(df)
    out = {}
    for c in cats:
        sub = df[df["Major Crime Head"] == c].groupby("MonthDate")["Commits"].sum().reindex(months).fillna(0)
        out[c] = sub.values
    return labels, out


# ---------------------------------------------------------------- FEATURE 3: anomaly detection (statistical)
def zscore_anomalies(df, top_n_cats=15, z_thresh=1.8):
    cats = top_categories(df, top_n_cats).index.tolist()
    labels, series = category_monthly(df, cats)
    rows = []
    for c in cats:
        vals = series[c]
        mean, std = vals.mean(), vals.std()
        if std == 0 or mean < 5:
            continue
        z = (vals - mean) / std
        for i, zi in enumerate(z):
            if zi > z_thresh and vals[i] > mean * 1.3:
                rows.append(dict(category=c, month=labels[i], value=vals[i],
                                  historical_avg=round(mean, 1),
                                  pct_above_avg=round((vals[i]-mean)/mean*100, 1),
                                  z_score=round(zi, 2)))
    return pd.DataFrame(rows).sort_values("z_score", ascending=False) if rows else pd.DataFrame(
        columns=["category", "month", "value", "historical_avg", "pct_above_avg", "z_score"])


# ---------------------------------------------------------------- FEATURE 4 (NEW): ML anomaly detection (Isolation Forest)
def isolation_forest_anomalies(df, top_n_cats=15, contamination=0.08):
    """Multivariate anomaly detection across categories jointly — catches unusual
    month-level *combinations* of categories, not just single-series spikes."""
    cats = top_categories(df, top_n_cats).index.tolist()
    labels, series = category_monthly(df, cats)
    X = np.column_stack([series[c] for c in cats])
    if X.shape[0] < 8:
        return pd.DataFrame(columns=["month", "anomaly_score", "flag"])
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    model.fit(X)
    scores = -model.score_samples(X)  # higher = more anomalous
    preds = model.predict(X)  # -1 anomaly, 1 normal
    out = pd.DataFrame({"month": labels, "anomaly_score": np.round(scores, 3), "flag": preds == -1})
    return out.sort_values("anomaly_score", ascending=False)


# ---------------------------------------------------------------- FEATURE 5: forecasting
def forecast_categories(df, cats, horizon=3):
    labels, series = category_monthly(df, cats)
    out = {}
    for c in cats:
        vals = series[c]
        n = min(12, len(vals))
        X = np.arange(n).reshape(-1, 1)
        y = vals[-n:]
        model = LinearRegression().fit(X, y)
        future_X = np.arange(n, n+horizon).reshape(-1, 1)
        preds = np.maximum(model.predict(future_X), 0)
        out[c] = dict(history=vals[-n:].tolist(), history_months=labels[-n:],
                       forecast=[round(p, 1) for p in preds], slope=round(model.coef_[0], 2))
    last = pd.Timestamp(month_labels(df)[0][-1])
    future_labels = [(last + pd.DateOffset(months=i)).strftime("%b-%y") for i in range(1, horizon+1)]
    return out, future_labels


# ---------------------------------------------------------------- Synthetic geo distribution (shared by features 6,7,8,9,10)
@lru_cache(maxsize=1)
def build_district_layer():
    df = load_raw()
    months, labels = month_labels(df)
    weights = np.array([DISTRICTS[d][2] for d in DIST_NAMES])
    weights = weights / weights.sum()
    rng = np.random.default_rng(7)

    spike_injections = {
        ("Bengaluru Urban", "THEFT", "Aug-22"): 2.8,
        ("Kalaburagi", "KIDNAPPING AND ABDUCTION", "Feb-22"): 3.2,
        ("Belagavi", "Robbery", "Nov-21"): 2.6,
        ("Ballari", "DACOITY", "Jun-22"): 2.9,
        ("Mysuru", "ASSAULT", "Oct-22"): 2.4,
    }
    month_major = df.groupby(["MonthDate", "Major Crime Head"])["Commits"].sum().reset_index()
    month_major = month_major[month_major["Commits"] > 0]

    dmc = {}  # (district, cat, month) -> value
    for _, row in month_major.iterrows():
        m_label = pd.Timestamp(row["MonthDate"]).strftime("%b-%y")
        cat, total = row["Major Crime Head"], row["Commits"]
        props = rng.dirichlet(weights * 20)
        for d, v in zip(DIST_NAMES, props * total):
            boost = spike_injections.get((d, cat, m_label), 1.0)
            dmc[(d, cat, m_label)] = dmc.get((d, cat, m_label), 0) + v * boost

    district_totals, district_cat_totals = {}, {}
    for (d, cat, m), v in dmc.items():
        district_totals[d] = district_totals.get(d, 0) + v
        district_cat_totals.setdefault(d, {})
        district_cat_totals[d][cat] = district_cat_totals[d].get(cat, 0) + v

    last3, prior9 = labels[-3:], (labels[-12:-3] if len(labels) >= 12 else labels[:-3])
    all_cats = df["Major Crime Head"].unique().tolist()
    rows = []
    for d in DIST_NAMES:
        recent = sum(dmc.get((d, c, m), 0) for c in all_cats for m in last3)
        prior = sum(dmc.get((d, c, m), 0) for c in all_cats for m in prior9)
        prior_avg_scaled = (prior/len(prior9))*len(last3) if prior9 else 1
        pct_change = ((recent-prior_avg_scaled)/prior_avg_scaled*100) if prior_avg_scaled > 0 else 0
        top_cat = max(district_cat_totals.get(d, {"N/A": 0}).items(), key=lambda kv: kv[1])[0]
        rows.append(dict(
            district=d, lat=DISTRICTS[d][0], lng=DISTRICTS[d][1],
            total=round(district_totals.get(d, 0), 1), recent_3mo=round(recent, 1),
            pct_change_vs_avg=round(pct_change, 1),
            is_hotspot=bool(pct_change > 25 and recent > 20),
            top_category=top_cat, population_lakh=POP_LAKH[d], urban_pct=URBAN_PCT[d],
            literacy_pct=LITERACY_PCT[d],
            crime_rate_per_lakh=round(district_totals.get(d, 0)/POP_LAKH[d], 2)
        ))
    ddf = pd.DataFrame(rows)

    max_recent = ddf["recent_3mo"].max() or 1
    vol = ddf["recent_3mo"]/max_recent*55
    trend = ddf["pct_change_vs_avg"].clip(-20, 80)/80*30
    trend = trend.clip(lower=0)
    urban = ddf["urban_pct"]/100*15
    ddf["risk_score"] = (vol+trend+urban).round(1).clip(upper=100)
    ddf["risk_band"] = pd.cut(ddf["risk_score"], bins=[-1, 25, 45, 65, 101],
                               labels=["Low", "Moderate", "High", "Critical"])

    station_types = ["Town", "City East", "City West", "Rural", "Traffic", "Women's Safety"]
    district_stations = {}
    for d in DIST_NAMES:
        n_st = 3 if DISTRICTS[d][2] < 0.3 else (4 if DISTRICTS[d][2] < 0.5 else 6)
        stations = random.sample(station_types, n_st)
        tot = district_totals.get(d, 1)
        splits = rng.dirichlet(np.ones(n_st)*3)*tot
        district_stations[d] = pd.DataFrame({"station": [f"{d} {s} PS" for s in stations],
                                              "total": np.round(splits, 1)}).sort_values("total", ascending=False)

    heat_points = []
    for (d, cat, m), v in dmc.items():
        n_pts = min(int(round(v/8)), 40)
        lat0, lng0 = DISTRICTS[d][0], DISTRICTS[d][1]
        for _ in range(n_pts):
            heat_points.append((lat0+rng.normal(0, 0.12), lng0+rng.normal(0, 0.12), m, cat, d))
    heat_df = pd.DataFrame(heat_points, columns=["lat", "lng", "month", "category", "district"])
    if len(heat_df) > 6000:
        heat_df = heat_df.sample(6000, random_state=1)

    return ddf, district_stations, heat_df, dmc


# ---------------------------------------------------------------- FEATURE 6 (NEW): KMeans hotspot clustering
def cluster_hotspots(k=4):
    ddf, *_ = build_district_layer()
    X = ddf[["recent_3mo", "pct_change_vs_avg", "crime_rate_per_lakh"]].copy()
    X = (X - X.mean()) / X.std().replace(0, 1)
    model = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    out = ddf.copy()
    out["cluster"] = model.labels_

    order = out.groupby("cluster")["risk_score"].mean().sort_values().index.tolist()
    base_names = ["Low-Intensity", "Emerging", "Elevated", "Priority Deployment", "Strategic Watch", "Rapid Response"]
    names = [base_names[i] if i < len(base_names) else f"Cluster {i + 1}" for i in range(len(order))]
    remap = {cluster: names[i] for i, cluster in enumerate(order)}
    out["cluster_label"] = out["cluster"].map(remap)
    return out


# ---------------------------------------------------------------- FEATURE 7: network / link analysis
@lru_cache(maxsize=1)
def build_network():
    df = load_raw()
    network_cats = ["THEFT", "KIDNAPPING AND ABDUCTION", "Murder", "DACOITY", "Robbery", "ATTEMPT TO MURDER"]
    mo_pool = df[df["Major Crime Head"].isin(network_cats)]["Minor Crime Head"].dropna().unique().tolist()
    mo_pool = [m for m in mo_pool if m and m.lower() != "others"][:40]
    first_names = ["A.Kumar","R.Naik","S.Gowda","M.Reddy","P.Shetty","V.Rao","K.Hegde","D.Patil",
                   "N.Iyer","J.Bhat","T.Shastry","L.Poojary","G.Achar","H.Kulkarni","B.Nayak","C.Salian"]
    rng = np.random.default_rng(11)
    suspects = []
    for i in range(1, 46):
        home = random.choice(DIST_NAMES)
        n_inc = int(rng.choice([1,1,1,2,2,3,4,5], p=[.32,.15,.1,.15,.1,.08,.06,.04]))
        juris = list({home, *random.sample(DIST_NAMES, min(n_inc, 4))})
        suspects.append(dict(id=f"S{i:03d}", label=f"{random.choice(first_names)}-{i:03d}", type="suspect",
                              home_district=home, n_incidents=n_inc, jurisdictions=juris,
                              mo_tags=random.sample(mo_pool, k=min(3, len(mo_pool))),
                              repeat_offender=n_inc >= 2, primary_crime=random.choice(network_cats)))
    victims = [dict(id=f"V{i:03d}", label=f"Victim-{i:03d}", type="victim", district=random.choice(DIST_NAMES))
               for i in range(1, 61)]
    locations = [dict(id=f"L{i:02d}", label=d, type="location") for i, d in enumerate(DIST_NAMES, 1)]

    edges, inc_id = [], 1
    for s in suspects:
        vpool = random.sample(victims, k=min(s["n_incidents"], len(victims)))
        for j in range(s["n_incidents"]):
            v = vpool[j % len(vpool)]
            loc_d = s["jurisdictions"][j % len(s["jurisdictions"])]
            loc_id = next(l["id"] for l in locations if l["label"] == loc_d)
            edges.append(dict(source=s["id"], target=v["id"], incident=f"INC{inc_id:04d}", crime=s["primary_crime"]))
            edges.append(dict(source=s["id"], target=loc_id, incident=f"INC{inc_id:04d}", crime=s["primary_crime"]))
            inc_id += 1
    for _ in range(14):
        a, b = random.sample(suspects, 2)
        edges.append(dict(source=a["id"], target=b["id"], incident="ASSOC", crime="co-offender link"))

    return dict(nodes=suspects+victims+locations, edges=edges, suspects=suspects)


# ---------------------------------------------------------------- FEATURE 8: socio-economic correlation
def socioeconomic_table():
    ddf, *_ = build_district_layer()
    return ddf[["district", "urban_pct", "literacy_pct", "population_lakh", "crime_rate_per_lakh", "risk_band"]]


# ---------------------------------------------------------------- FEATURE 9 (NEW): repeat-offender MO signature matching
def mo_signature_matches():
    """Finds suspects who share >=2 identical MO tags despite operating in
    different home districts — a lightweight stand-in for cross-jurisdiction
    pattern matching investigators currently do by memory."""
    net = build_network()
    suspects = net["suspects"]
    matches = []
    for i in range(len(suspects)):
        for j in range(i+1, len(suspects)):
            a, b = suspects[i], suspects[j]
            shared = set(a["mo_tags"]) & set(b["mo_tags"])
            if len(shared) >= 2 and a["home_district"] != b["home_district"]:
                matches.append(dict(suspect_a=a["label"], suspect_b=b["label"],
                                     district_a=a["home_district"], district_b=b["home_district"],
                                     shared_mo=", ".join(shared), n_shared=len(shared)))
    return pd.DataFrame(matches).sort_values("n_shared", ascending=False) if matches else pd.DataFrame(
        columns=["suspect_a","suspect_b","district_a","district_b","shared_mo","n_shared"])


# ---------------------------------------------------------------- FEATURE 10 (NEW): resource deployment recommender
def deployment_recommendations(n_units=10):
    """Simple proportional-allocation optimizer: distributes a fixed pool of
    patrol/investigation units across districts weighted by risk score,
    with a minimum floor so no district gets zero coverage."""
    ddf, *_ = build_district_layer()
    d = ddf.sort_values("risk_score", ascending=False).copy()
    floor = 1
    remaining = n_units - floor*len(d)
    if remaining < 0:
        remaining = 0
    weights = d["risk_score"] / d["risk_score"].sum()
    d["recommended_units"] = floor + np.floor(weights*remaining).astype(int)
    # distribute any leftover units to the highest-risk districts
    leftover = n_units - d["recommended_units"].sum()
    idx = d.index[:max(leftover, 0)]
    d.loc[idx, "recommended_units"] += 1
    d["shift_focus"] = np.where(d["pct_change_vs_avg"] > 25, "Night patrol + rapid response",
                          np.where(d["urban_pct"] > 50, "Traffic + urban beat", "Rural patrol + community liaison"))
    return d[["district","risk_score","risk_band","recommended_units","shift_focus","top_category"]].reset_index(drop=True)


# ---------------------------------------------------------------- meta
def meta_summary():
    df = load_raw()
    _, labels = month_labels(df)
    return dict(total_records=len(df), total_commits=float(df["Commits"].sum()),
                n_categories=df["Major Crime Head"].nunique(),
                month_range=f"{labels[0]} to {labels[-1]}", n_months=len(labels), n_districts=len(DIST_NAMES))


def taxonomy_table(top_n=200):
    df = load_raw()
    t = (df.groupby(["Major Crime Head", "Crime Head and Section"])["Commits"]
           .sum().reset_index().sort_values("Commits", ascending=False))
    return t.head(top_n)
