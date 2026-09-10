"""Live upload validation and inference using the project's existing model contract."""
from __future__ import annotations

import io
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "best_itransformer.pth"
DATA_PATH = ROOT / "Processed_Data"
REQUIRED_COLUMNS = ["Year", "Month_No", "Month", "Round", "State", "Station Code", "Station Name", "DO", "pH", "BOD"]
FEATURES = ["DO", "pH", "BOD"]
LOOKBACK = 12
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


class LivePredictionError(Exception):
    def __init__(self, message: str, code: str = "live_prediction_error"):
        super().__init__(message)
        self.code = code


@dataclass
class LiveResult:
    upload_id: str
    input_year: int
    input_month_no: int
    input_month: str
    forecast_year: int
    forecast_month_no: int
    forecast_month: str
    predictions: list[dict]
    warnings: int
    high_hotspots: int
    forecast_months_summary: str = ""


def next_month(year: int, month_no: int) -> tuple[int, int]:
    return (year + 1, 1) if month_no == 12 else (year, month_no + 1)


def get_forecast_schedule(input_year: int, input_month_no: int) -> list[tuple[int, int]]:
    # Only forecast for the immediate next month
    return [next_month(input_year, input_month_no)]


def calculate_continuous_wqi(do, ph, bod) -> float:
    if pd.isna(do) or pd.isna(ph) or pd.isna(bod):
        return 85.0
    try:
        do, ph, bod = float(do), float(ph), float(bod)
    except (ValueError, TypeError):
        return 85.0

    if do >= 8.5:
        q_do = 100.0
    elif do >= 6.0:
        q_do = 75.0 + (do - 6.0) / 2.5 * 25.0
    elif do >= 4.0:
        q_do = 50.0 + (do - 4.0) / 2.0 * 25.0
    else:
        q_do = max(0.0, (do / 4.0) * 50.0)

    if 7.0 <= ph <= 8.0:
        q_ph = 100.0
    elif 6.5 <= ph < 7.0:
        q_ph = 90.0 + (ph - 6.5) / 0.5 * 10.0
    elif 8.0 < ph <= 8.5:
        q_ph = 100.0 - (ph - 8.0) / 0.5 * 15.0
    else:
        q_ph = max(0.0, 85.0 - abs(ph - 7.5) * 20.0)

    if bod <= 1.5:
        q_bod = 100.0
    elif bod <= 3.0:
        q_bod = 100.0 - (bod - 1.5) / 1.5 * 25.0
    elif bod <= 5.0:
        q_bod = 75.0 - (bod - 3.0) / 2.0 * 25.0
    else:
        q_bod = max(0.0, 50.0 - (bod - 5.0) * 10.0)

    return round(0.40 * q_do + 0.30 * q_ph + 0.30 * q_bod, 2)


def calculate_wqi(do, ph, bod) -> float:
    return calculate_continuous_wqi(do, ph, bod)


def classify_wqi(wqi: float) -> str:
    if wqi >= 90:
        return "Excellent"
    if wqi >= 70:
        return "Good"
    if wqi >= 50:
        return "Moderate"
    if wqi >= 25:
        return "Poor"
    return "Very Poor"


def hotspot_level(wqi: float, violation_percentage: float, bod: float = 0.0, do: float = 10.0) -> str:
    if (wqi < 85 and violation_percentage >= 75) or wqi < 70 or bod > 5.0 or do < 4.0:
        return "High Hotspot"
    if (wqi < 90 and violation_percentage >= 25) or violation_percentage > 0 or wqi < 85 or bod > 3.0:
        return "Moderate Hotspot"
    return "Low / No Hotspot"


def validate_upload(raw: bytes) -> tuple[pd.DataFrame, int, int]:
    if not raw:
        raise LivePredictionError("The uploaded CSV is empty.", "empty_file")
    try:
        frame = pd.read_csv(io.BytesIO(raw))
    except Exception:
        raise LivePredictionError("The file is not a readable CSV.", "invalid_csv")

    frame.columns = [str(c).strip() for c in frame.columns]

    alias_map = {
        "station code": "Station Code",
        "station_code": "Station Code",
        "station code ": "Station Code",
        "station name": "Station Name",
        "station_name": "Station Name",
        "month_no": "Month_No",
        "month no": "Month_No",
        "month": "Month",
        "year": "Year",
        "round": "Round",
        "round_no": "Round",
        "state": "State",
        "do": "DO",
        "ph": "pH",
        "bod": "BOD",
    }
    rename_cols = {}
    for c in frame.columns:
        low = c.lower().strip()
        if low in alias_map and c != alias_map[low]:
            rename_cols[c] = alias_map[low]
    if rename_cols:
        frame = frame.rename(columns=rename_cols)

    if "Round" not in frame.columns:
        frame["Round"] = 1
    if "Month" not in frame.columns and "Month_No" in frame.columns:
        frame["Month"] = pd.to_numeric(frame["Month_No"], errors="coerce").apply(
            lambda m: MONTHS[int(m) - 1] if pd.notna(m) and 1 <= int(m) <= 12 else "Unknown"
        )

    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise LivePredictionError(f"Missing required CSV columns: {', '.join(missing)}.", "missing_columns")
    if frame.empty:
        raise LivePredictionError("The uploaded CSV contains no records.", "empty_file")

    frame = frame[REQUIRED_COLUMNS].copy()
    for col in ["Year", "Month_No", "Round", *FEATURES]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    if frame[["Year", "Month_No", "Round", *FEATURES]].isna().any().any():
        raise LivePredictionError("Year, month, round, DO, pH, and BOD cannot be empty or non-numeric.", "invalid_numeric_value")

    if (frame["Year"] < 1900).any() or (frame["Year"] > 2100).any():
        raise LivePredictionError("Year values must be between 1900 and 2100.", "invalid_year")
    if (~frame["Month_No"].between(1, 12)).any():
        raise LivePredictionError("Month_No values must be between 1 and 12.", "invalid_month")
    if (frame[FEATURES] < 0).any().any():
        raise LivePredictionError("DO, pH, and BOD cannot be negative.", "invalid_numeric_value")

    frame["Station Code"] = frame["Station Code"].astype(str).str.strip()
    frame["Station Name"] = frame["Station Name"].astype(str).str.strip()
    frame["State"] = frame["State"].astype(str).str.strip()
    frame["Year"] = frame["Year"].astype(int)
    frame["Month_No"] = frame["Month_No"].astype(int)
    frame["Round"] = frame["Round"].astype(int)
    frame["Month"] = frame["Month_No"].apply(lambda m: MONTHS[m - 1])

    months = frame[["Year", "Month_No"]].drop_duplicates()
    if len(months) != 1:
        raise LivePredictionError("Upload exactly one latest input month per file.", "multiple_input_months")

    input_year = int(months.iloc[0]["Year"])
    input_month_no = int(months.iloc[0]["Month_No"])
    return frame, input_year, input_month_no


def _load_model():
    if not MODEL_PATH.exists():
        raise LivePredictionError("The existing forecasting model file is unavailable.", "model_missing")
    try:
        import joblib
        import torch
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from itransformer_model import iTransformer
        scaler_x = joblib.load(DATA_PATH / "scaler_X.pkl")
        scaler_y = joblib.load(DATA_PATH / "scaler_y.pkl")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = iTransformer()
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()
        return model, scaler_x, scaler_y, torch, device
    except LivePredictionError:
        raise
    except Exception:
        raise LivePredictionError("The existing forecasting model could not be loaded.", "model_load_error")


def _get_history_fallback(station_code: str) -> pd.DataFrame:
    for filename in ["Final_Water_Quality_Dataset.csv", "Test_2025_Dataset.csv"]:
        p = DATA_PATH / filename
        if p.exists():
            try:
                df = pd.read_csv(p)
                df["Station Code"] = df["Station Code"].astype(str)
                sub = df[df["Station Code"] == str(station_code)].copy()
                if not sub.empty:
                    for col in FEATURES:
                        sub[col] = pd.to_numeric(sub[col], errors="coerce")
                    sub = sub.dropna(subset=FEATURES).sort_values(["Year", "Month_No"])
                    return sub
            except Exception:
                pass
    return pd.DataFrame()


def predict(frame: pd.DataFrame, input_year: int, input_month_no: int, history: pd.DataFrame, upload_id: str | None = None) -> LiveResult:
    schedule = get_forecast_schedule(input_year, input_month_no)
    model, scaler_x, scaler_y, torch, device = _load_model()
    upload_id = upload_id or str(uuid.uuid4())
    predictions = []

    for station_code, uploaded_station in frame.groupby("Station Code"):
        code_str = str(station_code)
        prior = pd.DataFrame()
        if history is not None and not history.empty and "Station Code" in history.columns:
            prior = history[history["Station Code"].astype(str) == code_str].copy()

        if len(prior) < (LOOKBACK - len(uploaded_station)):
            csv_prior = _get_history_fallback(code_str)
            if not csv_prior.empty:
                prior = pd.concat([csv_prior, prior], ignore_index=True)

        combined = pd.concat([prior, uploaded_station], ignore_index=True)
        if "Round" in combined.columns:
            combined = combined.drop_duplicates(["Year", "Month_No", "Round"], keep="last").sort_values(["Year", "Month_No", "Round"])
        month_records = combined.drop_duplicates(["Year", "Month_No"], keep="last").sort_values(["Year", "Month_No"])

        if len(month_records) < LOOKBACK:
            if month_records.empty:
                pad_row = uploaded_station[FEATURES].iloc[-1:].to_numpy(dtype=float)
            else:
                pad_row = month_records[FEATURES].iloc[:1].to_numpy(dtype=float)
            needed = LOOKBACK - len(month_records)
            pad_seq = np.repeat(pad_row, needed, axis=0)
            avail_seq = month_records[FEATURES].to_numpy(dtype=float)
            sequence = np.vstack([pad_seq, avail_seq])[-LOOKBACK:]
        else:
            sequence = month_records[FEATURES].tail(LOOKBACK).to_numpy(dtype=float)

        curr_seq = sequence.copy()
        station_name = str(uploaded_station.iloc[-1].get("Station Name", f"Station {code_str}"))
        state = str(uploaded_station.iloc[-1].get("State", ""))

        for f_year, f_month_no in schedule:
            try:
                scaled = scaler_x.transform(curr_seq).reshape(1, LOOKBACK, len(FEATURES))
                tensor = torch.tensor(scaled, dtype=torch.float32, device=device)
                with torch.no_grad():
                    output = model(tensor).detach().cpu().numpy()
                values = scaler_y.inverse_transform(output)[0]
            except Exception:
                raise LivePredictionError(f"Prediction failed for station {code_str}.", "prediction_error")

            pred_do = max(0.1, round(float(values[0]), 3))
            pred_ph = max(1.0, min(14.0, round(float(values[1]), 3)))
            pred_bod = max(0.1, round(float(values[2]), 3))

            wqi = round(calculate_continuous_wqi(pred_do, pred_ph, pred_bod), 2)
            do_status = "Compliant" if pred_do >= 5.0 else "Violation"
            ph_status = "Compliant" if 6.5 <= pred_ph <= 8.5 else "Violation"
            bod_status = "Compliant" if pred_bod <= 3.0 else "Violation"
            violations = sum(status == "Violation" for status in [do_status, ph_status, bod_status])
            violation_percentage = round((violations / 3.0) * 100, 2)
            hotspot = hotspot_level(wqi, violation_percentage, bod=pred_bod, do=pred_do)

            if hotspot == "High Hotspot" or wqi < 70.0 or violations >= 2 or pred_bod > 5.0 or pred_do < 4.0:
                severity = "High Risk"
                is_alert = True
            elif hotspot == "Moderate Hotspot" or violations >= 1 or wqi < 85.0 or pred_bod > 3.0:
                severity = "Warning"
                is_alert = True
            else:
                severity = "Normal"
                is_alert = False

            f_month_name = MONTHS[f_month_no - 1]
            predictions.append({
                "Station Code": code_str,
                "Station Name": station_name,
                "State": state,
                "Input_Year": input_year,
                "Input_Month_No": input_month_no,
                "Input_Month": MONTHS[input_month_no - 1],
                "Forecast_Year": f_year,
                "Forecast_Month_No": f_month_no,
                "Forecast_Month": f_month_name,
                "Predicted_DO": pred_do,
                "Predicted_pH": pred_ph,
                "Predicted_BOD": pred_bod,
                "Predicted_WQI": wqi,
                "WQI_Class": classify_wqi(wqi),
                "Hotspot_Level": hotspot,
                "Severity": severity,
                "Is_Alert": is_alert,
                "CPCB_DO_Status": do_status,
                "CPCB_pH_Status": ph_status,
                "CPCB_BOD_Status": bod_status,
                "CPCB_Violation_Percent": violation_percentage,
            })

            curr_seq = np.vstack([curr_seq[1:], [[pred_do, pred_ph, pred_bod]]])

    if not predictions:
        raise LivePredictionError("No station predictions could be generated.", "no_predictions")

    high_hotspots = sum(item["Severity"] == "High Risk" for item in predictions)
    warnings = sum(item["Is_Alert"] for item in predictions)

    first_f_year, first_f_month_no = schedule[0]
    last_f_year, last_f_month_no = schedule[-1]
    if len(schedule) > 1:
        forecast_months_summary = f"{MONTHS[first_f_month_no - 1]} - {MONTHS[last_f_month_no - 1]} {last_f_year}"
        forecast_month_label = f"{MONTHS[first_f_month_no - 1]} - {MONTHS[last_f_month_no - 1]}"
    else:
        forecast_months_summary = f"{MONTHS[first_f_month_no - 1]} {first_f_year}"
        forecast_month_label = MONTHS[first_f_month_no - 1]

    return LiveResult(
        upload_id=upload_id,
        input_year=input_year,
        input_month_no=input_month_no,
        input_month=MONTHS[input_month_no - 1],
        forecast_year=first_f_year,
        forecast_month_no=first_f_month_no,
        forecast_month=forecast_month_label,
        predictions=predictions,
        warnings=warnings,
        high_hotspots=high_hotspots,
        forecast_months_summary=forecast_months_summary,
    )


def timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

