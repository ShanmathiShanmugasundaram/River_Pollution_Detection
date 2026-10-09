import os
import io
from pathlib import Path
from functools import lru_cache
import json
from datetime import datetime, timezone

import pandas as pd
from flask import Flask, jsonify, request, send_file, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from .live_prediction import LivePredictionError, calculate_wqi, classify_wqi, next_month, predict, timestamp, validate_upload
except ImportError:
    from live_prediction import LivePredictionError, calculate_wqi, classify_wqi, next_month, predict, timestamp, validate_upload

BACKEND_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Processed_Data"

for env_candidate in (WEBSITE_DIR / ".env", BACKEND_DIR / ".env", ROOT / ".env"):
    if env_candidate.exists():
        load_dotenv(env_candidate)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-only-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
frontend_origins = {
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
}
frontend_origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})


@app.before_request
def handle_api_preflight():
    if request.method == "OPTIONS" and request.path.startswith("/api/"):
        response = jsonify({})
        response.status_code = 204
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "Access-Control-Request-Headers", "Content-Type, Cache-Control, Authorization, *"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS, DELETE"
        response.headers["Vary"] = "Origin"
        return response


@app.after_request
def allow_local_frontend(response):
    origin = request.headers.get("Origin")
    if origin and request.path.startswith("/api/"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "Access-Control-Request-Headers", "Content-Type, Cache-Control, Authorization, *"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS, DELETE"
        response.headers.add("Vary", "Origin")
    return response



def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        return round(value, 3)
    return value


def records(frame):
    return [{key: clean_value(value) for key, value in row.items()} for row in frame.to_dict(orient="records")]


@lru_cache(maxsize=16)
def load_csv(name):
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {name}")
    return pd.read_csv(path)


def forecast_frame():
    return load_csv("Forecast_2026_WQI.csv").copy()


def apply_filters(frame):
    state = request.args.get("state")
    station = request.args.get("station")
    month = request.args.get("month")
    if state:
        frame = frame[frame["State"].astype(str).str.casefold() == state.casefold()]
    if station:
        frame = frame[frame["Station Code"].astype(str) == str(station)]
    if month:
        frame = frame[frame["Forecast_Month_No"].astype(str) == str(month)]
    return frame


def hotspot_frame():
    frame = load_csv("Hotspot_Analysis_2026.csv").copy()
    frame["Station Code"] = frame["Station Code"].astype(str)
    return frame


def station_rows():
    forecast = forecast_frame()
    forecast["Station Code"] = forecast["Station Code"].astype(str)
    hotspots = hotspot_frame()
    grouped = forecast.groupby(["Station Code", "Station Name", "State"], as_index=False).agg(
        forecast_months=("Forecast_Month_No", "nunique"),
        average_wqi=("Pred_WQI", "mean"),
        average_do=("Pred_DO", "mean"),
        average_ph=("Pred_pH", "mean"),
        average_bod=("Pred_BOD", "mean"),
    )
    hotspot_columns = ["Station Code", "Hotspot_Level", "CPCB_Violation_Percent", "Mean_WQI", "Mean_BOD"]
    grouped = grouped.merge(hotspots[hotspot_columns], on="Station Code", how="left")
    grouped = grouped.rename(columns={"Station Code": "station_code", "Station Name": "station_name", "State": "state"})
    grouped["hotspot_level"] = grouped["Hotspot_Level"].fillna("Low/No Hotspot")
    return grouped


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "data_source": "Processed_Data CSV exports", "mysql_configured": bool(os.getenv("MYSQL_HOST"))})


@lru_cache(maxsize=1)
def master_stations_frame():
    df_hist = load_csv("Final_Water_Quality_Dataset.csv")
    df_2025 = load_csv("Test_2025_Dataset.csv")
    df_2026 = load_csv("Forecast_2026_WQI.csv")
    master = pd.concat([
        df_2025[["Station Code", "Station Name", "State"]],
        df_hist[["Station Code", "Station Name", "State"]],
        df_2026[["Station Code", "Station Name", "State"]],
    ]).drop_duplicates(subset=["Station Code"]).reset_index(drop=True)
    master["station_code"] = master["Station Code"].astype(str)
    master["station_name"] = master["Station Name"]
    master["state"] = master["State"]
    return master


@lru_cache(maxsize=32)
def stations_for_year(year_int):
    master = master_stations_frame().copy()
    
    # Pre-calculated 2025 baseline
    d25 = load_csv("Test_2025_Dataset.csv").copy()
    for col in ["DO", "pH", "BOD"]:
        d25[col] = pd.to_numeric(d25[col], errors="coerce")
    d25 = d25.dropna(subset=["DO", "pH", "BOD"])
    d25["Pred_WQI"] = d25.apply(lambda r: calculate_wqi(float(r["DO"]), float(r["pH"]), float(r["BOD"])), axis=1)
    base_2025 = d25.groupby("Station Code")["Pred_WQI"].mean().to_dict()
    
    # Pre-calculated 2026 baseline
    d26 = load_csv("Forecast_2026_WQI.csv").copy()
    d26["Pred_WQI"] = pd.to_numeric(d26["Pred_WQI"], errors="coerce")
    base_2026 = d26.groupby("Station Code")["Pred_WQI"].mean().to_dict()
    
    curr = {}
    if year_int == 2026:
        curr = base_2026
    elif year_int == 2025:
        curr = base_2025
    else:
        dh = load_csv("Final_Water_Quality_Dataset.csv").copy()
        for col in ["DO", "pH", "BOD"]:
            dh[col] = pd.to_numeric(dh[col], errors="coerce")
        sub = dh[dh["Year"] == year_int].dropna(subset=["DO", "pH", "BOD"]).copy()
        if not sub.empty:
            sub["WQI"] = sub.apply(lambda r: calculate_wqi(float(r["DO"]), float(r["pH"]), float(r["BOD"])), axis=1)
            curr = sub.groupby("Station Code")["WQI"].mean().to_dict()
            
    rows = []
    for _, s in master.iterrows():
        raw_code = s["Station Code"]
        code_int = int(raw_code) if str(raw_code).isdigit() else raw_code
        wqi = curr.get(code_int) or curr.get(str(raw_code)) or base_2025.get(code_int) or base_2026.get(raw_code) or base_2026.get(str(raw_code)) or 75.0
        rows.append({
            "station_code": str(raw_code),
            "station_name": s["station_name"],
            "state": s["state"],
            "average_wqi": round(float(wqi), 1),
            "hotspot_level": "Historical observation" if year_int <= 2025 else "Forecast 2026"
        })
    return pd.DataFrame(rows)


@app.get("/api/stations")
def stations():
    year = request.args.get("year")
    if year and year.isdigit() and 2014 <= int(year) <= 2026:
        frame = stations_for_year(int(year)).copy()
    else:
        frame = station_rows()
    state = request.args.get("state")
    level = request.args.get("hotspot_level")
    search = request.args.get("search")
    if state:
        frame = frame[frame["state"].str.casefold() == state.casefold()]
    if level:
        frame = frame[frame["hotspot_level"].str.casefold() == level.casefold()]
    if search:
        mask = frame["station_name"].str.contains(search, case=False, na=False) | frame["station_code"].str.contains(search, case=False, na=False)
        frame = frame[mask]
    response = jsonify(records(frame))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/stations/<station_code>")
def station(station_code):
    frame = station_rows()
    match = frame[frame["station_code"] == str(station_code)]
    if not match.empty:
        return jsonify(records(match)[0])

    master = master_stations_frame()
    m = master[master["station_code"] == str(station_code)]
    if not m.empty:
        s_row = m.iloc[0]
        all_s = stations_for_year(2025)
        w_match = all_s[all_s["station_code"] == str(station_code)]
        avg_w = float(w_match.iloc[0]["average_wqi"]) if not w_match.empty else 75.0
        return jsonify({
            "station_code": str(station_code),
            "station_name": s_row["station_name"],
            "state": s_row["state"],
            "forecast_months": 12,
            "average_wqi": clean_value(avg_w),
            "average_do": None,
            "average_ph": None,
            "average_bod": None,
            "hotspot_level": "Historical observation",
        })
    return jsonify({"error": "Station not found"}), 404


MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def score_do(value):
    if value >= 8:
        return 100.0
    elif value >= 6:
        return 80.0
    elif value >= 4:
        return 60.0
    elif value >= 2:
        return 40.0
    else:
        return 20.0


def score_ph(value):
    if 6.5 <= value <= 8.5:
        return 100.0
    elif (6.0 <= value < 6.5) or (8.5 < value <= 9.0):
        return 80.0
    elif (5.5 <= value < 6.0) or (9.0 < value <= 9.5):
        return 60.0
    else:
        return 40.0


def score_bod(value):
    if value <= 2:
        return 100.0
    elif value <= 3:
        return 80.0
    elif value <= 5:
        return 60.0
    elif value <= 8:
        return 40.0
    else:
        return 20.0


def calculate_wqi(do, ph, bod):
    if pd.isna(do) or pd.isna(ph) or pd.isna(bod):
        return 85.0
    try:
        do, ph, bod = float(do), float(ph), float(bod)
    except (ValueError, TypeError):
        return 85.0
    return round(0.40 * score_do(do) + 0.30 * score_ph(ph) + 0.30 * score_bod(bod), 2)


calculate_continuous_wqi = calculate_wqi


def _fetch_monthly_raw(station_code, year_int):
    code_str = str(station_code)
    if year_int == 2026:
        d26 = load_csv("Forecast_2026_WQI.csv").copy()
        sub = d26[d26["Station Code"].astype(str) == code_str].copy()
        if not sub.empty:
            for col in ["Pred_DO", "Pred_pH", "Pred_BOD", "Pred_WQI"]:
                sub[col] = pd.to_numeric(sub[col], errors="coerce")
            grp = sub.groupby("Forecast_Month_No", as_index=False).agg({
                "Pred_DO": "mean", "Pred_pH": "mean", "Pred_BOD": "mean", "Pred_WQI": "mean",
                "Forecast_Month": "first", "Station Code": "first", "Station Name": "first", "State": "first"
            }).sort_values("Forecast_Month_No")
            grp["Forecast_Year"] = 2026
            grp["DO"] = grp["Pred_DO"]
            grp["pH"] = grp["Pred_pH"]
            grp["BOD"] = grp["Pred_BOD"]
            grp["WQI"] = grp["Pred_WQI"]
            return grp.reset_index(drop=True)
        return None

    if year_int == 2025:
        d25 = load_csv("Test_2025_Dataset.csv").copy()
        for col in ["DO", "pH", "BOD"]:
            d25[col] = pd.to_numeric(d25[col], errors="coerce")
        sub = d25[d25["Station Code"].astype(str) == code_str].dropna(subset=["DO", "pH", "BOD"]).copy()
        if not sub.empty:
            sub["WQI"] = sub.apply(lambda r: calculate_continuous_wqi(r["DO"], r["pH"], r["BOD"]), axis=1)
            grp = sub.groupby("Month_No", as_index=False).agg({
                "DO": "mean", "pH": "mean", "BOD": "mean", "WQI": "mean",
                "Month": "first", "Station Code": "first", "Station Name": "first", "State": "first"
            }).sort_values("Month_No")
            grp["Forecast_Year"] = 2025
            grp["Forecast_Month_No"] = grp["Month_No"]
            grp["Forecast_Month"] = grp["Month"]
            grp["Pred_DO"] = grp["DO"]
            grp["Pred_pH"] = grp["pH"]
            grp["Pred_BOD"] = grp["BOD"]
            grp["Pred_WQI"] = grp["WQI"]
            return grp
        return None

    dh = load_csv("Final_Water_Quality_Dataset.csv").copy()
    for col in ["DO", "pH", "BOD"]:
        dh[col] = pd.to_numeric(dh[col], errors="coerce")
    sub = dh[(dh["Station Code"].astype(str) == code_str) & (dh["Year"] == year_int)].dropna(subset=["DO", "pH", "BOD"]).copy()
    if not sub.empty:
        sub["WQI"] = sub.apply(lambda r: calculate_continuous_wqi(r["DO"], r["pH"], r["BOD"]), axis=1)
        grp = sub.groupby("Month_No", as_index=False).agg({
            "DO": "mean", "pH": "mean", "BOD": "mean", "WQI": "mean",
            "Station Code": "first", "Station Name": "first", "State": "first"
        }).sort_values("Month_No")
        grp["Forecast_Year"] = year_int
        grp["Forecast_Month_No"] = grp["Month_No"]
        grp["Forecast_Month"] = grp["Month_No"].apply(lambda m: MONTH_NAMES[int(m)-1] if 1 <= int(m) <= 12 else f"Month {m}")
        grp["Pred_DO"] = grp["DO"]
        grp["Pred_pH"] = grp["pH"]
        grp["Pred_BOD"] = grp["BOD"]
        grp["Pred_WQI"] = grp["WQI"]
        return grp
    return None


def _expand_to_12_months(grp, year_int):
    if grp is None or grp.empty:
        return grp
    if len(grp) == 12:
        return grp

    meta_name = grp["Station Name"].iloc[0] if "Station Name" in grp else ""
    meta_code = grp["Station Code"].iloc[0] if "Station Code" in grp else ""
    meta_state = grp["State"].iloc[0] if "State" in grp else ""

    do_season =  [0.6,  0.5,  0.2, -0.2, -0.4, -0.5, -0.3, -0.2,  0.0,  0.2,  0.4,  0.6]
    ph_season =  [0.1,  0.1,  0.0, -0.1, -0.1, -0.1,  0.0,  0.0,  0.1,  0.1,  0.1,  0.1]
    bod_season = [-0.2, -0.2,  0.0,  0.2,  0.3,  0.4,  0.1,  0.0, -0.1, -0.2, -0.3, -0.3]

    months_df = pd.DataFrame({
        "Forecast_Month_No": list(range(1, 13)),
        "Forecast_Month": MONTH_NAMES,
        "Forecast_Year": year_int
    })
    merged = pd.merge(months_df, grp, on="Forecast_Month_No", how="left", suffixes=("", "_old"))
    merged["Station Code"] = meta_code
    merged["Station Name"] = meta_name
    merged["State"] = meta_state
    merged["Forecast_Year"] = year_int

    base_do = grp["DO"].mean() if "DO" in grp and pd.notna(grp["DO"].mean()) else 7.5
    base_ph = grp["pH"].mean() if "pH" in grp and pd.notna(grp["pH"].mean()) else 7.8
    base_bod = grp["BOD"].mean() if "BOD" in grp and pd.notna(grp["BOD"].mean()) else 2.5

    for i in range(12):
        m_no = i + 1
        if m_no not in grp["Forecast_Month_No"].values:
            merged.loc[merged["Forecast_Month_No"] == m_no, "DO"] = round(max(2.0, base_do + do_season[i]), 2)
            merged.loc[merged["Forecast_Month_No"] == m_no, "pH"] = round(min(9.0, max(6.0, base_ph + ph_season[i])), 2)
            merged.loc[merged["Forecast_Month_No"] == m_no, "BOD"] = round(max(0.5, base_bod + bod_season[i]), 2)

    for col in ["DO", "pH", "BOD"]:
        merged[col] = merged[col].interpolate().bfill().ffill().round(2)
        merged[f"Pred_{col}"] = merged[col]

    merged["WQI"] = merged.apply(lambda r: round(calculate_continuous_wqi(r["DO"], r["pH"], r["BOD"]), 2), axis=1)
    merged["Pred_WQI"] = merged["WQI"]
    return merged


@lru_cache(maxsize=256)
def get_station_monthly(station_code, year_int):
    # 1. Try requested year directly
    res = _fetch_monthly_raw(station_code, year_int)
    if res is not None and not res.empty:
        return _expand_to_12_months(res, year_int)

    # 2. Try 2025 (contains all 112 stations)
    if year_int != 2025:
        res = _fetch_monthly_raw(station_code, 2025)
        if res is not None and not res.empty:
            res = res.copy()
            res["Forecast_Year"] = year_int
            return _expand_to_12_months(res, year_int)

    # 3. Try 2026
    if year_int != 2026:
        res = _fetch_monthly_raw(station_code, 2026)
        if res is not None and not res.empty:
            res = res.copy()
            res["Forecast_Year"] = year_int
            return _expand_to_12_months(res, year_int)

    # 4. Check any available historical year
    dh = load_csv("Final_Water_Quality_Dataset.csv")
    sub = dh[dh["Station Code"].astype(str) == str(station_code)]
    if not sub.empty:
        avail_years = sorted(sub["Year"].dropna().unique(), reverse=True)
        for y in avail_years:
            res = _fetch_monthly_raw(station_code, int(y))
            if res is not None and not res.empty:
                res = res.copy()
                res["Forecast_Year"] = year_int
                return _expand_to_12_months(res, year_int)

    return None


@app.get("/api/forecast")
@app.get("/api/forecast/")
def forecast():
    station_code = request.args.get("station")
    year = request.args.get("year", "2026")
    year_int = int(year) if year.isdigit() and 2014 <= int(year) <= 2026 else 2026
    if station_code:
        frame = get_station_monthly(station_code, year_int)
        if frame is None or frame.empty:
            return jsonify([])
        return jsonify(records(frame))
    frame = apply_filters(forecast_frame())
    return jsonify(records(frame))


@app.get("/api/forecast/<station_code>")
def station_forecast(station_code=None):
    if not station_code:
        return forecast()
    year = request.args.get("year", "2026")
    year_int = int(year) if year.isdigit() and 2014 <= int(year) <= 2026 else 2026
    frame = get_station_monthly(station_code, year_int)
    if frame is None or frame.empty:
        return jsonify([])
    return jsonify(records(frame))



@lru_cache(maxsize=32)
def get_basin_monthly_wqi(year_int):
    if year_int == 2026:
        d26 = load_csv("Forecast_2026_WQI.csv").copy()
        for col in ["Pred_DO", "Pred_pH", "Pred_BOD", "Pred_WQI"]:
            d26[col] = pd.to_numeric(d26[col], errors="coerce")
        grp = d26.groupby("Forecast_Month_No", as_index=False).agg({
            "Pred_DO": "mean",
            "Pred_pH": "mean",
            "Pred_BOD": "mean",
            "Pred_WQI": "mean",
            "Forecast_Month": "first"
        }).sort_values("Forecast_Month_No")
        grp["Month_No"] = grp["Forecast_Month_No"]
        grp["Month"] = grp["Forecast_Month"]
        grp["DO"] = grp["Pred_DO"]
        grp["pH"] = grp["Pred_pH"]
        grp["BOD"] = grp["Pred_BOD"]
        grp["WQI"] = grp["Pred_WQI"]
        grp["Year"] = 2026
        return grp.reset_index(drop=True)
    elif year_int == 2025:
        d25 = load_csv("Test_2025_Dataset.csv").copy()
        for col in ["DO", "pH", "BOD"]:
            d25[col] = pd.to_numeric(d25[col], errors="coerce")
        d25 = d25.dropna(subset=["DO", "pH", "BOD"]).copy()
        d25["WQI"] = d25.apply(lambda r: calculate_wqi(r["DO"], r["pH"], r["BOD"]), axis=1)
        grp = d25.groupby("Month_No", as_index=False).agg({
            "DO": "mean", "pH": "mean", "BOD": "mean", "WQI": "mean", "Month": "first"
        }).sort_values("Month_No")
        grp["DO"] = grp["DO"].round(2)
        grp["pH"] = grp["pH"].round(2)
        grp["BOD"] = grp["BOD"].round(2)
        grp["WQI"] = grp["WQI"].round(2)
    else:
        dh = load_csv("Final_Water_Quality_Dataset.csv").copy()
        for col in ["DO", "pH", "BOD"]:
            dh[col] = pd.to_numeric(dh[col], errors="coerce")
        sub = dh[dh["Year"] == year_int].dropna(subset=["DO", "pH", "BOD"]).copy()
        if sub.empty:
            sub = dh.dropna(subset=["DO", "pH", "BOD"]).copy()
        sub["WQI"] = sub.apply(lambda r: calculate_wqi(r["DO"], r["pH"], r["BOD"]), axis=1)
        grp = sub.groupby("Month_No", as_index=False).agg({
            "DO": "mean", "pH": "mean", "BOD": "mean", "WQI": "mean"
        }).sort_values("Month_No")
        grp["Month"] = grp["Month_No"].apply(lambda m: MONTH_NAMES[int(m)-1] if 1 <= int(m) <= 12 else f"Month {m}")
        grp["DO"] = grp["DO"].round(2)
        grp["pH"] = grp["pH"].round(2)
        grp["BOD"] = grp["BOD"].round(2)
        grp["WQI"] = grp["WQI"].round(2)

    months_df = pd.DataFrame({
        "Month_No": list(range(1, 13)),
        "Month": MONTH_NAMES
    })
    merged = pd.merge(months_df, grp, on="Month_No", how="left", suffixes=("", "_old"))
    if "Month_old" in merged:
        merged = merged.drop(columns=["Month_old"])
    for col in ["DO", "pH", "BOD", "WQI"]:
        merged[col] = merged[col].interpolate().bfill().ffill().round(2)

    merged["Pred_DO"] = merged["DO"]
    merged["Pred_pH"] = merged["pH"]
    merged["Pred_BOD"] = merged["BOD"]
    merged["Pred_WQI"] = merged["WQI"]
    merged["Year"] = year_int
    return merged.reset_index(drop=True)


@lru_cache(maxsize=1)
def get_all_years_wqi_summary():
    out = []
    for y in range(2026, 2013, -1):
        df = get_basin_monthly_wqi(y)
        best_row = df.loc[df["WQI"].idxmax()]
        lowest_row = df.loc[df["WQI"].idxmin()]
        out.append({
            "year": y,
            "average_wqi": round(float(df["WQI"].mean()), 2),
            "best_month": str(best_row["Month"]),
            "best_wqi": round(float(best_row["WQI"]), 2),
            "lowest_month": str(lowest_row["Month"]),
            "lowest_wqi": round(float(lowest_row["WQI"]), 2),
            "is_forecast": y == 2026
        })
    return out


@app.get("/api/wqi/monthly-trend")
def wqi_monthly_trend():
    year = request.args.get("year", "2026")
    year_int = int(year) if year.isdigit() and 2014 <= int(year) <= 2026 else 2026
    station_code = request.args.get("station")

    station_name = "All Monitoring Stations (Basin Average)"
    if station_code:
        st_df = get_station_monthly(station_code, year_int)
        if st_df is not None and not st_df.empty:
            df = st_df.copy()
            df["Month_No"] = df["Forecast_Month_No"]
            df["Month"] = df["Forecast_Month"]
            if "Station Name" in df and pd.notna(df["Station Name"].iloc[0]):
                station_name = f"{df['Station Name'].iloc[0]} ({station_code})"
        else:
            df = get_basin_monthly_wqi(year_int)
    else:
        df = get_basin_monthly_wqi(year_int)

    df = df.reset_index(drop=True)
    monthly_records = []
    for _, r in df.iterrows():
        monthly_records.append({
            "month_no": int(r["Month_No"]),
            "month": str(r["Month"]),
            "WQI": round(float(r["WQI"]), 2),
            "DO": round(float(r["DO"]), 2),
            "pH": round(float(r["pH"]), 2),
            "BOD": round(float(r["BOD"]), 2),
            "Pred_WQI": float(r["WQI"]),
            "Pred_DO": float(r["DO"]),
            "Pred_pH": float(r["pH"]),
            "Pred_BOD": float(r["BOD"])
        })

    best_row = df.loc[df["WQI"].idxmax()]
    lowest_row = df.loc[df["WQI"].idxmin()]

    return jsonify({
        "year": year_int,
        "is_forecast": year_int == 2026,
        "station_code": station_code,
        "station_name": station_name,
        "average_wqi": round(float(df["WQI"].mean()), 2),
        "best_month": str(best_row["Month"]),
        "best_wqi": round(float(best_row["WQI"]), 2),
        "lowest_month": str(lowest_row["Month"]),
        "lowest_wqi": round(float(lowest_row["WQI"]), 2),
        "monthly": monthly_records,
        "all_years": get_all_years_wqi_summary()
    })


@app.get("/api/wqi")
def wqi():
    year = request.args.get("year")
    station = request.args.get("station")
    if year or station:
        return wqi_monthly_trend()
    return jsonify(records(apply_filters(forecast_frame())))


@app.get("/api/wqi/<station_code>")
def station_wqi(station_code):
    frame = forecast_frame()
    frame = frame[frame["Station Code"].astype(str) == str(station_code)]
    if frame.empty:
        return jsonify({"error": "WQI forecast not found"}), 404
    return jsonify(records(frame[["Forecast_Month_No", "Forecast_Month", "Pred_WQI", "Predicted_Class"]]))


@app.get("/api/hotspots")
def hotspots():
    frame = hotspot_frame()
    level = request.args.get("level")
    state = request.args.get("state")
    if level:
        frame = frame[frame["Hotspot_Level"].str.casefold() == level.casefold()]
    if state:
        frame = frame[frame["State"].str.casefold() == state.casefold()]
    return jsonify(records(frame))


@app.get("/api/hotspots/<station_code>")
def station_hotspot(station_code):
    frame = hotspot_frame()
    match = frame[frame["Station Code"] == str(station_code)]
    if match.empty:
        return jsonify({"error": "Hotspot analysis not found"}), 404
    return jsonify(records(match)[0])


@app.get("/api/cpcb-compliance")
def cpcb():
    return jsonify(records(hotspot_frame()))


@app.get("/api/biological")
def biological():
    name = "Seasonal_WQI_Saprobic_Validation.csv"
    frame = load_csv(name)
    state = request.args.get("state")
    if state and "State" in frame:
        frame = frame[frame["State"].astype(str).str.casefold() == state.casefold()]
    return jsonify(records(frame))


@app.get("/api/biological/<station_code>")
def station_biological(station_code):
    frame = load_csv("Seasonal_WQI_Saprobic_Validation.csv")
    if "Station_Code" not in frame:
        return jsonify([])
    match = frame[frame["Station_Code"].astype(str) == str(station_code)]
    return jsonify(records(match))


@app.get("/api/dashboard-summary")
def dashboard_summary():
    stations_data = station_rows()
    forecast = forecast_frame()
    hotspots = hotspot_frame()
    levels = hotspots["Hotspot_Level"].value_counts().to_dict()
    return jsonify({
        "total_stations": int(len(stations_data)),
        "high_hotspots": int(levels.get("High Hotspot", 0)),
        "moderate_hotspots": int(levels.get("Moderate Hotspot", 0)),
        "low_hotspots": int(levels.get("Low/No Hotspot", 0)),
        "average_predicted_wqi": clean_value(forecast["Pred_WQI"].mean()),
        "forecast_months": int(forecast["Forecast_Month_No"].nunique()),
        "average_do": clean_value(forecast["Pred_DO"].mean()),
        "average_ph": clean_value(forecast["Pred_pH"].mean()),
        "average_bod": clean_value(forecast["Pred_BOD"].mean()),
    })


@app.get("/api/state-summary")
def state_summary():
    forecast = forecast_frame()
    hotspots = hotspot_frame()
    by_state = forecast.groupby("State", as_index=False).agg(
        station_count=("Station Code", "nunique"), average_wqi=("Pred_WQI", "mean"), average_bod=("Pred_BOD", "mean"),
        average_do=("Pred_DO", "mean"), average_ph=("Pred_pH", "mean"),
    )
    state_hotspots = hotspots.groupby("State", as_index=False).agg(
        predicted_hotspots=("Hotspot_Level", lambda values: int((values != "Low/No Hotspot").sum())),
        criterion_exceedance=("CPCB_Violation_Percent", "mean"),
    )
    return jsonify(records(by_state.merge(state_hotspots, on="State", how="left")))


@app.get("/api/early-warning")
def early_warning():
    frame = hotspot_frame().copy()
    def warning(row):
        if row["Hotspot_Level"] == "High Hotspot" or row["CPCB_Violation_Percent"] >= 75:
            return "High Warning"
        if row["Hotspot_Level"] == "Moderate Hotspot" or row["CPCB_Violation_Percent"] >= 50:
            return "Warning"
        if row["CPCB_Violation_Percent"] > 0:
            return "Watch"
        return "Normal"
    frame["Warning_Level"] = frame.apply(warning, axis=1)
    return jsonify(records(frame))


def mysql_connection():
    if not os.getenv("MYSQL_HOST"):
        raise LivePredictionError("Live prediction requires MySQL credentials in the backend environment.", "mysql_not_configured")
    try:
        import pymysql
        return pymysql.connect(
            host=os.environ["MYSQL_HOST"], port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"],
            database=os.getenv("MYSQL_DATABASE", "ganga_water_quality"),
            cursorclass=pymysql.cursors.DictCursor, autocommit=False,
        )
    except LivePredictionError:
        raise
    except Exception as exc:
        app.logger.exception("MySQL connection failed: %s", exc)
        raise LivePredictionError("The live prediction database is unavailable.", "mysql_unavailable")


from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "Authentication required."}), 401
        if user.get("role") != "admin":
            return jsonify({"error": "Forbidden: Admin access required."}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.get("/api/auth/me")
def auth_me():
    user = session.get("user")
    return jsonify({"authenticated": bool(user), "user": user})


def user_payload(row):
    return {
        "user_id": row["user_id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "mobile": row.get("mobile"),
        "role": row.get("role", "user") or "user",
        "status": row.get("status", "active") or "active",
    }


@app.post("/api/auth/signup")
def auth_signup():
    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    mobile = str(payload.get("mobile", "")).strip() or None
    password = str(payload.get("password", ""))
    if not full_name or len(full_name) > 120:
        return jsonify({"error": "Enter a valid name."}), 400
    if "@" not in email or len(email) > 255:
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must contain at least 8 characters."}), 400
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "An account with this email already exists."}), 409
            cursor.execute(
                "INSERT INTO users (full_name, email, mobile, password_hash, role, status) VALUES (%s,%s,%s,%s,%s,%s)",
                (full_name, email, mobile, generate_password_hash(password), "user", "active"),
            )
            user_id = cursor.lastrowid
        connection.commit()
        session["user"] = {
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "mobile": mobile,
            "role": "user",
            "status": "active",
        }
        return jsonify({"authenticated": True, "user": session["user"]}), 201
    finally:
        connection.close()


@app.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, full_name, email, mobile, password_hash, role, status FROM users WHERE email=%s",
                (email,),
            )
            user = cursor.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Email or password is incorrect."}), 401
        if user.get("status") in ["inactive", "deactivated"]:
            return jsonify({"error": "Your account has been deactivated. Please contact an administrator."}), 403
        session["user"] = user_payload(user)
        return jsonify({"authenticated": True, "user": session["user"]})
    finally:
        connection.close()


@app.post("/api/auth/logout")
def auth_logout():
    session.pop("user", None)
    return jsonify({"authenticated": False})


@app.put("/api/auth/profile")
def auth_profile():
    current = session.get("user")
    if not current:
        return jsonify({"error": "Please log in first."}), 401
    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name", "")).strip()
    mobile = str(payload.get("mobile", "")).strip() or None
    if not full_name:
        return jsonify({"error": "Name cannot be empty."}), 400
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET full_name=%s, mobile=%s WHERE user_id=%s", (full_name, mobile, current["user_id"]))
        connection.commit()
        current.update({"full_name": full_name, "mobile": mobile})
        session["user"] = current
        return jsonify({"authenticated": True, "user": current})
    finally:
        connection.close()


def historical_for_stations(cursor, station_codes):
    if not station_codes:
        return pd.DataFrame(columns=["Station Code", "Station Name", "State", "Year", "Month_No", "Round", "DO", "pH", "BOD"])
    rows = []
    if cursor:
        try:
            placeholders = ",".join(["%s"] * len(station_codes))
            cursor.execute(
                f"SELECT station_code AS `Station Code`, station_name AS `Station Name`, state AS State, observation_year AS Year, observation_month_no AS Month_No, round_no AS Round, do_value AS DO, ph_value AS `pH`, bod_value AS BOD FROM historical_water_quality WHERE station_code IN ({placeholders})",
                list(station_codes),
            )
            rows = list(cursor.fetchall())
            cursor.execute(
                f"SELECT station_code AS `Station Code`, station_name AS `Station Name`, state AS State, input_year AS Year, input_month_no AS Month_No, round_no AS Round, do_value AS DO, ph_value AS `pH`, bod_value AS BOD FROM live_input_data WHERE station_code IN ({placeholders})",
                list(station_codes),
            )
            rows.extend(list(cursor.fetchall()))
        except Exception:
            rows = []

    # Supplement from Processed_Data CSVs if missing or sparse
    found_codes = {str(r.get("Station Code")) for r in rows}
    missing_codes = [c for c in station_codes if str(c) not in found_codes]
    if missing_codes or len(rows) < (12 * len(station_codes)):
        try:
            csv_path = DATA / "Final_Water_Quality_Dataset.csv"
            if csv_path.exists():
                hist_df = pd.read_csv(csv_path)
                hist_df["Station Code"] = hist_df["Station Code"].astype(str)
                sub_df = hist_df[hist_df["Station Code"].isin([str(c) for c in station_codes])]
                if not sub_df.empty:
                    for _, r in sub_df.iterrows():
                        rows.append({
                            "Station Code": str(r["Station Code"]),
                            "Station Name": str(r.get("Station Name", "")),
                            "State": str(r.get("State", "")),
                            "Year": int(r["Year"]),
                            "Month_No": int(r["Month_No"]),
                            "Round": int(r.get("Round", 1)),
                            "DO": float(r["DO"]),
                            "pH": float(r["pH"]),
                            "BOD": float(r["BOD"]),
                        })
        except Exception:
            pass

    if not rows:
        return pd.DataFrame(columns=["Station Code", "Station Name", "State", "Year", "Month_No", "Round", "DO", "pH", "BOD"])
    return pd.DataFrame(rows)


LIVE_STORE_FILE = DATA / "live_predictions_store.json"


def _save_to_json_store(upload_info, frame, predictions, notifications_list):
    try:
        data = {"uploads": [], "predictions": {}, "notifications": []}
        if LIVE_STORE_FILE.exists():
            try:
                with open(LIVE_STORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["uploads"].insert(0, upload_info)
        data["predictions"][upload_info["upload_id"]] = predictions
        data["notifications"] = notifications_list + data.get("notifications", [])
        with open(LIVE_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print("Warning: could not save to JSON store:", e)


def save_live_result(connection, frame, result, filename):
    average_wqi = sum(item["Predicted_WQI"] for item in result.predictions) / len(result.predictions)
    current_user = session.get("user")
    uploader_name = current_user.get("full_name") if current_user else "User"
    uploader_id = current_user.get("user_id") if current_user else None
    record_count = len(frame)

    upload_summary = {
        "upload_id": result.upload_id,
        "filename": filename,
        "uploaded_by": uploader_name,
        "record_count": record_count,
        "status": "Completed",
        "input_year": result.input_year,
        "input_month_no": result.input_month_no,
        "input_month": result.input_month,
        "forecast_year": result.forecast_year,
        "forecast_month_no": result.forecast_month_no,
        "forecast_month": result.forecast_month,
        "stations_processed": len(frame["Station Code"].unique()),
        "average_wqi": round(average_wqi, 2),
        "warnings": result.warnings,
        "high_hotspots": result.high_hotspots,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    notifications_to_save = []
    for item in result.predictions:
        # Strictly high-risk forecast alerts (no moderate warning alerts)
        if item.get("Severity") == "High Risk" or item.get("Hotspot_Level") == "High Hotspot":
            sev = "High Risk"
            f_label = f"{item['Forecast_Month']} {item['Forecast_Year']}"
            msg = f"A high-risk water quality condition is predicted for {item['Station Name']} ({item['Station Code']}) for the forecast period ({f_label}). (Predicted WQI: {item['Predicted_WQI']:.1f}, BOD: {item['Predicted_BOD']:.2f} mg/L, DO: {item['Predicted_DO']:.2f} mg/L)."
            title = "High-Risk Water Quality Prediction"
            n_type = "HIGH_RISK_WARNING"
            notifications_to_save.append({
                "upload_id": result.upload_id,
                "station_code": str(item["Station Code"]),
                "station_name": str(item["Station Name"]),
                "state": str(item["State"]),
                "severity": sev,
                "input_month": result.input_month,
                "forecast_month": f_label,
                "predicted_wqi": float(item["Predicted_WQI"]),
                "predicted_do": float(item["Predicted_DO"]),
                "predicted_ph": float(item["Predicted_pH"]),
                "predicted_bod": float(item["Predicted_BOD"]),
                "hotspot_level": str(item["Hotspot_Level"]),
                "title": title,
                "notification_type": n_type,
                "message": msg,
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # Save to JSON store as resilient backup
    _save_to_json_store(upload_summary, frame, result.predictions, notifications_to_save)

    if connection:
        with connection.cursor() as cursor:
            # Retrieve all admin user IDs
            cursor.execute("SELECT user_id FROM users WHERE role='admin'")
            admin_rows = cursor.fetchall()
            admin_ids = [r["user_id"] for r in admin_rows] if admin_rows else []

            cursor.execute("DELETE FROM live_uploads WHERE upload_id=%s", (result.upload_id,))
            cursor.execute(
                """INSERT INTO live_uploads 
                   (upload_id, filename, uploaded_by, record_count, status, input_year, input_month_no, input_month, 
                    forecast_year, forecast_month_no, forecast_month, stations_processed, average_wqi, warnings, high_hotspots) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (result.upload_id, filename, uploader_name, record_count, "Completed", result.input_year, result.input_month_no, result.input_month, result.forecast_year, result.forecast_month_no, result.forecast_month, len(frame["Station Code"].unique()), average_wqi, result.warnings, result.high_hotspots),
            )
            for _, row in frame.iterrows():
                cursor.execute(
                    "INSERT INTO live_input_data (upload_id, station_code, station_name, state, input_year, input_month_no, round_no, do_value, ph_value, bod_value) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (result.upload_id, str(row["Station Code"]), row["Station Name"], row["State"], int(row["Year"]), int(row["Month_No"]), int(row["Round"]), float(row["DO"]), float(row["pH"]), float(row["BOD"])),
                )
            for item in result.predictions:
                cursor.execute(
                    """INSERT INTO live_predictions 
                       (upload_id, station_code, station_name, state, forecast_year, forecast_month_no, 
                        predicted_do, predicted_ph, predicted_bod, predicted_wqi, wqi_class, hotspot_level, 
                        cpcb_do_status, cpcb_ph_status, cpcb_bod_status, cpcb_violation_percent) 
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON DUPLICATE KEY UPDATE 
                        predicted_do=VALUES(predicted_do), predicted_ph=VALUES(predicted_ph), 
                        predicted_bod=VALUES(predicted_bod), predicted_wqi=VALUES(predicted_wqi), 
                        wqi_class=VALUES(wqi_class), hotspot_level=VALUES(hotspot_level)""",
                    (result.upload_id, str(item["Station Code"]), item["Station Name"], item["State"], int(item["Forecast_Year"]), int(item["Forecast_Month_No"]), float(item["Predicted_DO"]), float(item["Predicted_pH"]), float(item["Predicted_BOD"]), float(item["Predicted_WQI"]), item["WQI_Class"], item["Hotspot_Level"], item["CPCB_DO_Status"], item["CPCB_pH_Status"], item["CPCB_BOD_Status"], float(item["CPCB_Violation_Percent"])),
                )

            # Insert HIGH_RISK_WARNING notifications for each recipient
            recipients = set(admin_ids)
            if uploader_id:
                recipients.add(uploader_id)
            if not recipients:
                recipients = {None}

            for notif in notifications_to_save:
                for r_id in recipients:
                    cursor.execute(
                        """INSERT IGNORE INTO notifications 
                           (upload_id, recipient_user_id, notification_type, title, station_code, station_name, state, severity, 
                            input_month, forecast_month, predicted_wqi, predicted_do, predicted_ph, predicted_bod, 
                            hotspot_level, message, is_read) 
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE)""",
                        (notif["upload_id"], r_id, notif["notification_type"], notif["title"], notif["station_code"], notif["station_name"], notif["state"],
                         notif["severity"], notif["input_month"], notif["forecast_month"],
                         notif["predicted_wqi"], notif["predicted_do"], notif["predicted_ph"], notif["predicted_bod"],
                         notif["hotspot_level"], notif["message"]),
                    )
        connection.commit()

    try:
        get_station_monthly.cache_clear()
        get_basin_monthly_wqi.cache_clear()
        get_all_years_wqi_summary.cache_clear()
    except Exception:
        pass


@app.post("/api/live-prediction")
def live_prediction():
    connection = None
    try:
        upload = request.files.get("file")
        if upload is None or not upload.filename.lower().endswith(".csv"):
            raise LivePredictionError("Choose a CSV file to upload.", "invalid_file_type")
        frame, input_year, input_month_no = validate_upload(upload.read())
        try:
            connection = mysql_connection()
            with connection.cursor() as cursor:
                history = historical_for_stations(cursor, frame["Station Code"].unique().tolist())
        except Exception:
            connection = None
            history = historical_for_stations(None, frame["Station Code"].unique().tolist())

        result = predict(frame, input_year, input_month_no, history)
        save_live_result(connection, frame, result, upload.filename)
        return jsonify({
            "upload_id": result.upload_id,
            "input_month": result.input_month,
            "input_year": result.input_year,
            "forecast_month": result.forecast_month,
            "forecast_year": result.forecast_year,
            "forecast_months_summary": result.forecast_months_summary,
            "stations_processed": len(frame["Station Code"].unique()),
            "average_wqi": round(sum(item["Predicted_WQI"] for item in result.predictions) / len(result.predictions), 2),
            "warnings": result.warnings,
            "high_hotspots": result.high_hotspots,
            "predictions": result.predictions,
        }), 201
    except LivePredictionError as error:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        return jsonify({"error": str(error), "code": error.code}), 400
    except Exception as exc:
        import traceback
        traceback.print_exc()
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        return jsonify({"error": f"Live prediction could not be completed: {str(exc)}", "code": "live_prediction_failed"}), 500
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


@app.get("/api/live-predictions")
def live_predictions():
    try:
        connection = mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT upload_id, input_year, input_month, forecast_year, forecast_month, stations_processed, average_wqi, warnings, high_hotspots, created_at FROM live_uploads ORDER BY created_at DESC LIMIT 50")
                rows = cursor.fetchall()
                if rows:
                    return jsonify(records(pd.DataFrame(rows)))
        finally:
            connection.close()
    except Exception:
        pass

    # Fallback to JSON store
    if LIVE_STORE_FILE.exists():
        try:
            with open(LIVE_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data.get("uploads", []))
        except Exception:
            pass
    return jsonify([])


@app.get("/api/live-predictions/<upload_id>")
def live_prediction_result(upload_id):
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    try:
        connection = mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM live_uploads WHERE upload_id=%s", (upload_id,))
                upload_row = cursor.fetchone()
                cursor.execute("SELECT * FROM live_predictions WHERE upload_id=%s ORDER BY forecast_year ASC, forecast_month_no ASC, predicted_wqi ASC", (upload_id,))
                rows = cursor.fetchall()
                if rows:
                    formatted_preds = []
                    for r in rows:
                        m_no = int(r["forecast_month_no"])
                        m_name = month_names[m_no - 1] if 1 <= m_no <= 12 else str(m_no)
                        formatted_preds.append({
                            "Forecast_Year": int(r["forecast_year"]),
                            "Forecast_Month_No": m_no,
                            "Forecast_Month": m_name,
                            "Station Code": str(r["station_code"]),
                            "Station Name": r["station_name"],
                            "State": r["state"],
                            "Predicted_DO": float(r["predicted_do"]),
                            "Predicted_pH": float(r["predicted_ph"]),
                            "Predicted_BOD": float(r["predicted_bod"]),
                            "Predicted_WQI": float(r["predicted_wqi"]),
                            "WQI_Class": r["wqi_class"],
                            "Hotspot_Level": r["hotspot_level"],
                            "CPCB_DO_Status": r["cpcb_do_status"],
                            "CPCB_pH_Status": r["cpcb_ph_status"],
                            "CPCB_BOD_Status": r["cpcb_bod_status"],
                            "CPCB_Violation_Percent": float(r["cpcb_violation_percent"]),
                            "Severity": "High Risk" if r["hotspot_level"] == "High Hotspot" or r["predicted_wqi"] < 70 else ("Warning" if r["cpcb_violation_percent"] > 0 or r["hotspot_level"] == "Moderate Hotspot" else "Normal"),
                        })
                    if upload_row:
                        return jsonify({
                            "upload_id": upload_row["upload_id"],
                            "input_year": upload_row["input_year"],
                            "input_month": upload_row["input_month"],
                            "forecast_year": upload_row["forecast_year"],
                            "forecast_month": upload_row["forecast_month"],
                            "forecast_months_summary": f"{upload_row['input_month']} {upload_row['input_year']} → {upload_row['forecast_month']} {upload_row['forecast_year']}",
                            "stations_processed": upload_row["stations_processed"],
                            "average_wqi": float(upload_row["average_wqi"]),
                            "warnings": upload_row["warnings"],
                            "high_hotspots": upload_row["high_hotspots"],
                            "predictions": formatted_preds,
                        })
                    return jsonify({"upload_id": upload_id, "predictions": formatted_preds})
        finally:
            connection.close()
    except Exception:
        pass

    # Fallback to JSON store
    if LIVE_STORE_FILE.exists():
        try:
            with open(LIVE_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                upload_info = next((u for u in data.get("uploads", []) if u["upload_id"] == upload_id), None)
                preds = data.get("predictions", {}).get(upload_id, [])
                if upload_info and preds:
                    return jsonify({
                        **upload_info,
                        "predictions": preds,
                    })
                elif preds:
                    return jsonify({"upload_id": upload_id, "predictions": preds})
        except Exception:
            pass
    return jsonify({"error": "Upload not found"}), 404


def notification_query(extra=""):
    try:
        connection = mysql_connection()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM notifications {extra} ORDER BY created_at DESC LIMIT 100")
            data = records(pd.DataFrame(cursor.fetchall()))
        connection.close()
        if data:
            return data
    except Exception:
        pass

    # Fallback to JSON store
    if LIVE_STORE_FILE.exists():
        try:
            with open(LIVE_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                notifs = data.get("notifications", [])
                if "WHERE is_read=FALSE" in extra:
                    notifs = [n for n in notifs if not n.get("is_read", False)]
                elif "WHERE severity='High Risk'" in extra:
                    notifs = [n for n in notifs if n.get("severity") == "High Risk"]
                return notifs[:100]
        except Exception:
            pass
    return []



@app.get("/api/notifications")
def notifications():
    return jsonify(notification_query())


@app.get("/api/notifications/unread")
def unread_notifications():
    return jsonify(notification_query("WHERE is_read=FALSE"))


@app.get("/api/notifications/high-risk")
def high_risk_notifications():
    return jsonify(notification_query("WHERE severity='High Risk'"))


@app.get("/api/notifications/count")
def notification_count():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM notifications WHERE is_read=FALSE")
            return jsonify(cursor.fetchone())
    finally:
        connection.close()


@app.put("/api/notifications/<int:notification_id>/read")
def mark_notification_read(notification_id):
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE notifications SET is_read=TRUE WHERE notification_id=%s", (notification_id,))
        connection.commit()
        return jsonify({"status": "read"})
    finally:
        connection.close()


@app.put("/api/notifications/read-all")
def mark_all_notifications_read():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE notifications SET is_read=TRUE WHERE is_read=FALSE")
        connection.commit()
        return jsonify({"status": "read"})
    finally:
        connection.close()


# ==========================================
# ADMIN API ENDPOINTS (PROTECTED BY @admin_required)
# ==========================================

@app.get("/api/admin/summary")
@admin_required
def admin_summary():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            total_users = cursor.fetchone()["total_users"]
            cursor.execute("SELECT COUNT(*) AS active_users FROM users WHERE COALESCE(status, 'active') = 'active'")
            active_users = cursor.fetchone()["active_users"]
            cursor.execute("SELECT COUNT(*) AS total_alerts FROM notifications WHERE severity IN ('High Risk', 'Warning') OR notification_type = 'HIGH_RISK_WARNING'")
            total_alerts = cursor.fetchone()["total_alerts"]
            cursor.execute("SELECT COUNT(*) AS recent_uploads FROM live_uploads")
            recent_uploads = cursor.fetchone()["recent_uploads"]
            return jsonify({
                "total_users": total_users,
                "active_users": active_users,
                "total_alerts": total_alerts,
                "recent_uploads": recent_uploads,
            })
    finally:
        connection.close()


@app.get("/api/admin/users")
@admin_required
def admin_get_users():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, full_name, email, mobile, role, COALESCE(status, 'active') AS status, created_at FROM users ORDER BY created_at DESC"
            )
            users = cursor.fetchall()
            df = pd.DataFrame(users) if users else pd.DataFrame(columns=["user_id", "full_name", "email", "mobile", "role", "status", "created_at"])
            return jsonify(records(df))
    finally:
        connection.close()


@app.post("/api/admin/users")
@admin_required
def admin_create_user():
    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    mobile = str(payload.get("mobile", "")).strip() or None
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "user")).strip().lower()
    status = str(payload.get("status", "active")).strip().lower()

    if not full_name or len(full_name) > 120:
        return jsonify({"error": "Enter a valid full name."}), 400
    if "@" not in email or len(email) > 255:
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if role not in ["admin", "user"]:
        return jsonify({"error": "Role must be either 'admin' or 'user'."}), 400
    if status not in ["active", "inactive"]:
        status = "active"

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "An account with this email already exists."}), 409
            cursor.execute(
                "INSERT INTO users (full_name, email, mobile, password_hash, role, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (full_name, email, mobile, generate_password_hash(password), role, status),
            )
            new_id = cursor.lastrowid
        connection.commit()
        return jsonify({"status": "success", "user_id": new_id, "message": "User created successfully."}), 201
    finally:
        connection.close()


@app.put("/api/admin/users/<int:user_id>")
@admin_required
def admin_update_user(user_id):
    current_admin = session.get("user")
    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    mobile = str(payload.get("mobile", "")).strip() or None
    role = str(payload.get("role", "")).strip().lower()
    status = str(payload.get("status", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not full_name:
        return jsonify({"error": "Full name cannot be empty."}), 400
    if "@" not in email:
        return jsonify({"error": "Valid email is required."}), 400
    if role and role not in ["admin", "user"]:
        return jsonify({"error": "Role must be 'admin' or 'user'."}), 400
    if status and status not in ["active", "inactive"]:
        return jsonify({"error": "Status must be 'active' or 'inactive'."}), 400

    if current_admin and current_admin.get("user_id") == user_id and role == "user":
        return jsonify({"error": "You cannot demote your own admin account."}), 400

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email=%s AND user_id != %s", (email, user_id))
            if cursor.fetchone():
                return jsonify({"error": "Another user with this email already exists."}), 409

            if password and len(password) >= 8:
                cursor.execute(
                    "UPDATE users SET full_name=%s, email=%s, mobile=%s, role=%s, status=%s, password_hash=%s WHERE user_id=%s",
                    (full_name, email, mobile, role, status, generate_password_hash(password), user_id),
                )
            else:
                cursor.execute(
                    "UPDATE users SET full_name=%s, email=%s, mobile=%s, role=%s, status=%s WHERE user_id=%s",
                    (full_name, email, mobile, role, status, user_id),
                )
        connection.commit()
        return jsonify({"status": "success", "message": "User updated successfully."})
    finally:
        connection.close()


@app.put("/api/admin/users/<int:user_id>/status")
@admin_required
def admin_toggle_user_status(user_id):
    current_admin = session.get("user")
    if current_admin and current_admin.get("user_id") == user_id:
        return jsonify({"error": "You cannot deactivate your own admin account."}), 400

    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            if not new_status:
                cursor.execute("SELECT status FROM users WHERE user_id=%s", (user_id,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "User not found."}), 404
                curr = row.get("status") or "active"
                new_status = "inactive" if curr == "active" else "active"
            elif new_status not in ["active", "inactive"]:
                return jsonify({"error": "Status must be 'active' or 'inactive'."}), 400

            cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", (new_status, user_id))
        connection.commit()
        return jsonify({"status": "success", "new_status": new_status, "message": f"User status set to {new_status}."})
    finally:
        connection.close()


@app.delete("/api/admin/users/<int:user_id>")
@admin_required
def admin_delete_user(user_id):
    current_admin = session.get("user")
    if current_admin and current_admin.get("user_id") == user_id:
        return jsonify({"error": "You cannot delete your own admin account."}), 400

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        connection.commit()
        return jsonify({"status": "success", "message": "User deleted successfully."})
    finally:
        connection.close()


@app.get("/api/admin/datasets")
@admin_required
def admin_get_datasets():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    upload_id AS id,
                    filename AS file_name,
                    COALESCE(uploaded_by, 'System') AS uploaded_by,
                    created_at AS upload_date,
                    COALESCE(record_count, stations_processed) AS record_count,
                    COALESCE(status, 'Completed') AS status,
                    created_at,
                    stations_processed,
                    average_wqi,
                    warnings,
                    high_hotspots,
                    input_month,
                    input_year,
                    forecast_month,
                    forecast_year
                FROM live_uploads
                ORDER BY created_at DESC
            """)
            datasets = cursor.fetchall()
            df = pd.DataFrame(datasets) if datasets else pd.DataFrame(columns=["id", "file_name", "uploaded_by", "upload_date", "record_count", "status", "created_at"])
            return jsonify(records(df))
    finally:
        connection.close()


@app.delete("/api/admin/datasets/<dataset_id>")
@admin_required
def admin_delete_dataset(dataset_id):
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT upload_id, filename FROM live_uploads WHERE upload_id=%s", (dataset_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({"error": "Dataset not found."}), 404
            cursor.execute("DELETE FROM live_uploads WHERE upload_id=%s", (dataset_id,))
        connection.commit()
        return jsonify({"status": "success", "message": f"Dataset {target['filename']} removed successfully."})
    finally:
        connection.close()


@app.get("/api/admin/notifications")
@admin_required
def admin_get_notifications():
    current_admin = session.get("user")
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    notification_id AS id,
                    notification_id,
                    recipient_user_id,
                    COALESCE(notification_type, 'HIGH_RISK_WARNING') AS notification_type,
                    COALESCE(title, 'Water Quality Alert') AS title,
                    message,
                    station_code,
                    station_name,
                    state,
                    severity,
                    input_month,
                    forecast_month,
                    predicted_wqi,
                    predicted_do,
                    predicted_ph,
                    predicted_bod,
                    hotspot_level,
                    is_read,
                    read_at,
                    created_at
                FROM notifications
                WHERE (recipient_user_id = %s OR recipient_user_id IS NULL)
                  AND notification_type != 'USER_UPLOAD'
                  AND severity != 'Warning'
                  AND message NOT LIKE '%%Warning Alert%%'
                  AND message NOT LIKE '%%exceeds CPCB reference criteria%%'
                ORDER BY created_at DESC
                LIMIT 150
            """, (current_admin["user_id"],))
            notifs = cursor.fetchall()
            df = pd.DataFrame(notifs) if notifs else pd.DataFrame(columns=["id", "title", "message", "notification_type", "severity", "is_read", "created_at"])
            return jsonify(records(df))
    finally:
        connection.close()


@app.put("/api/admin/notifications/<int:notification_id>/read")
@admin_required
def admin_mark_notification_read(notification_id):
    current_admin = session.get("user")
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET is_read=TRUE, read_at=CURRENT_TIMESTAMP WHERE notification_id=%s AND (recipient_user_id=%s OR recipient_user_id IS NULL)",
                (notification_id, current_admin["user_id"]),
            )
        connection.commit()
        return jsonify({"status": "read", "message": "Notification marked as read."})
    finally:
        connection.close()


@app.put("/api/admin/notifications/read-all")
@admin_required
def admin_mark_all_notifications_read():
    current_admin = session.get("user")
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET is_read=TRUE, read_at=CURRENT_TIMESTAMP WHERE (recipient_user_id=%s OR recipient_user_id IS NULL) AND is_read=FALSE",
                (current_admin["user_id"],),
            )
        connection.commit()
        return jsonify({"status": "read", "message": "All notifications marked as read."})
    finally:
        connection.close()


@app.post("/api/admin/notifications/system")
@admin_required
def admin_create_system_message():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "System Message")).strip() or "System Message"
    message = str(payload.get("message", "")).strip()
    severity = str(payload.get("severity", "Info")).strip() or "Info"

    if not message:
        return jsonify({"error": "Message content is required."}), 400

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (recipient_user_id, notification_type, title, message, severity, is_read) VALUES (NULL, 'SYSTEM_MESSAGE', %s, %s, %s, FALSE)",
                (title, message, severity),
            )
        connection.commit()
        return jsonify({"status": "success", "message": "System notification broadcasted."}), 201
    finally:
        connection.close()


@app.get("/api/admin/user-folders")
@admin_required
def admin_get_user_folders():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id, full_name, email, role, COALESCE(status, 'active') AS status, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()

            cursor.execute("""
                SELECT upload_id, filename, uploaded_by, input_year, input_month, forecast_year, forecast_month, 
                       stations_processed, average_wqi, warnings, high_hotspots, COALESCE(record_count, stations_processed) AS record_count,
                       COALESCE(status, 'Completed') AS status, created_at 
                FROM live_uploads ORDER BY created_at DESC
            """)
            all_uploads = cursor.fetchall()

            user_folders = []
            for u in users:
                user_name = u["full_name"]
                user_email = u["email"]
                user_files = [
                    upl for upl in all_uploads 
                    if str(upl.get("uploaded_by", "")).lower() in [user_name.lower(), user_email.lower()]
                ]
                total_records = sum(int(f.get("record_count") or 0) for f in user_files)
                user_folders.append({
                    "user_id": u["user_id"],
                    "folder_name": f"{user_name.replace(' ', '_').lower()}_{u['user_id']}",
                    "full_name": user_name,
                    "email": user_email,
                    "role": u["role"],
                    "status": u["status"],
                    "member_since": u["created_at"],
                    "file_count": len(user_files),
                    "total_records": total_records,
                    "files": records(pd.DataFrame(user_files) if user_files else pd.DataFrame(columns=["upload_id", "filename", "created_at", "record_count", "status"])),
                })

            assigned_filenames = {f["upload_id"] for uf in user_folders for f in uf["files"]}
            system_files = [upl for upl in all_uploads if upl["upload_id"] not in assigned_filenames]
            if system_files:
                user_folders.append({
                    "user_id": 0,
                    "folder_name": "system_and_shared_uploads",
                    "full_name": "System & Legacy Data",
                    "email": "system@gangawatch.gov.in",
                    "role": "system",
                    "status": "active",
                    "member_since": None,
                    "file_count": len(system_files),
                    "total_records": sum(int(f.get("record_count") or 0) for f in system_files),
                    "files": records(pd.DataFrame(system_files)),
                })

            return jsonify(user_folders)
    finally:
        connection.close()


@app.get("/api/admin/system-messages")
@admin_required
def admin_get_system_messages():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    notification_id AS id,
                    title,
                    message,
                    severity,
                    created_at,
                    is_read
                FROM notifications
                WHERE notification_type = 'SYSTEM_MESSAGE'
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "title", "message", "severity", "created_at", "is_read"])
            return jsonify(records(df))
    finally:
        connection.close()


@app.delete("/api/admin/system-messages/<int:msg_id>")
@admin_required
def admin_delete_system_message(msg_id):
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM notifications WHERE notification_id=%s AND notification_type='SYSTEM_MESSAGE'", (msg_id,))
        connection.commit()
        return jsonify({"status": "success", "message": "System message deleted."})
    finally:
        connection.close()


@app.get("/api/admin/database/overview")
@admin_required
def admin_get_database_overview():
    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            table_stats = []
            tables = [
                ("users", "User Credentials & Roles"),
                ("stations", "Ganga Monitoring Stations Master"),
                ("historical_water_quality", "Historical Water Quality Records"),
                ("forecast_2026", "iTransformer 2026 Forecast Outputs"),
                ("wqi_predictions", "Predicted Water Quality Index Values"),
                ("hotspot_analysis", "CPCB Hotspot Classifications"),
                ("live_uploads", "User & Live Dataset Uploads"),
                ("live_input_data", "Uploaded Observation Records"),
                ("live_predictions", "Generated Live Predictions"),
                ("notifications", "System & Forecast Alert Notifications"),
            ]
            for tbl, desc in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) AS c FROM `{tbl}`")
                    cnt = cursor.fetchone()["c"]
                    table_stats.append({"table_name": tbl, "description": desc, "row_count": cnt})
                except Exception:
                    pass

            return jsonify({
                "database_name": os.getenv("MYSQL_DATABASE", "ganga_water_quality"),
                "host": os.getenv("MYSQL_HOST", "localhost"),
                "port": int(os.getenv("MYSQL_PORT", 3306)),
                "tables": table_stats,
            })
    finally:
        connection.close()


@app.errorhandler(Exception)
def handle_error(error):
    app.logger.exception(error)
    return jsonify({"error": "The data service could not complete this request."}), 500


@app.errorhandler(LivePredictionError)
def handle_live_prediction_error(error):
    status = 503 if error.code in {"mysql_not_configured", "mysql_unavailable"} else 400
    return jsonify({"error": str(error), "code": error.code}), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")
