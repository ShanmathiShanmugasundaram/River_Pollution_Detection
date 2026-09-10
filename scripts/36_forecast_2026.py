import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from itransformer_model import iTransformer


# =====================================================
# Paths
# =====================================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"

MODEL_PATH = PROJECT_DIR / "models" / "best_itransformer.pth"


# =====================================================
# Load Dataset
# =====================================================

df = pd.read_csv(
    DATA_FOLDER / "Test_2025_Dataset.csv"
)

print("=" * 50)
print("2025 DATA")
print("=" * 50)
print(df.shape)


# =====================================================
# Load Scalers
# =====================================================

scaler_X = joblib.load(
    DATA_FOLDER / "scaler_X.pkl"
)

scaler_y = joblib.load(
    DATA_FOLDER / "scaler_y.pkl"
)


# =====================================================
# Load Model
# =====================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model = iTransformer()

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=device
    )
)

model.to(device)
model.eval()

print("\nModel Loaded Successfully")


# =====================================================
# Forecast Settings
# =====================================================

features = [
    "DO",
    "pH",
    "BOD"
]

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

future_records = []


# =====================================================
# Forecast Each Station
# =====================================================

for station, station_df in df.groupby("Station Code"):

    station_df = station_df.sort_values(
        by=[
            "Year",
            "Month_No",
            "Round"
        ]
    )

    if len(station_df) < 12:
        continue

    sequence = station_df[features].values[-12:]

    station_name = station_df.iloc[-1]["Station Name"]
    state = station_df.iloc[-1]["State"]

    for month_no in range(1, 13):

        for round_no in [1, 2]:

            # -------------------------
            # Scale
            # -------------------------

            scaled = scaler_X.transform(sequence)

            X = scaled.reshape(
                1,
                12,
                3
            )

            X = torch.tensor(
                X,
                dtype=torch.float32
            ).to(device)

            # -------------------------
            # Predict
            # -------------------------

            with torch.no_grad():

                pred = model(X)

            pred = pred.cpu().numpy()

            pred = scaler_y.inverse_transform(pred)[0]

            future_records.append({

                "Forecast_Year": 2026,
                "Forecast_Month_No": month_no,
                "Forecast_Month": months[month_no - 1],
                "Forecast_Round": round_no,
                "State": state,
                "Station Code": station,
                "Station Name": station_name,
                "Pred_DO": round(float(pred[0]), 3),
                "Pred_pH": round(float(pred[1]), 3),
                "Pred_BOD": round(float(pred[2]), 3)

            })

            # -------------------------
            # Recursive Update
            # -------------------------

            sequence = np.vstack([
                sequence[1:],
                pred
            ])


# =====================================================
# Save
# =====================================================

forecast_df = pd.DataFrame(
    future_records
)

print("\n")
print("=" * 50)
print("2026 FORECAST")
print("=" * 50)

print(forecast_df.head())

print("\nTotal Predictions :", len(forecast_df))

forecast_df.to_csv(
    DATA_FOLDER / "Forecast_2026.csv",
    index=False
)

print("\nSaved Successfully")

print(
    DATA_FOLDER / "Forecast_2026.csv"
)