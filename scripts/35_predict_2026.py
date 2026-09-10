import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from itransformer_model import iTransformer


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"

MODEL_PATH = PROJECT_DIR / "models" / "best_itransformer.pth"


# ============================================
# Load Dataset
# ============================================

df = pd.read_csv(
    DATA_FOLDER / "Test_2025_Dataset.csv"
)

print("="*50)
print("2025 DATA")
print("="*50)
print(df.shape)


# ============================================
# Load Scalers
# ============================================

scaler_X = joblib.load(
    DATA_FOLDER / "scaler_X.pkl"
)

scaler_y = joblib.load(
    DATA_FOLDER / "scaler_y.pkl"
)


# ============================================
# Load Model
# ============================================

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
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


# ============================================
# Features
# ============================================

features = [
    "DO",
    "pH",
    "BOD"
]


results = []


# ============================================
# Predict Next Observation
# ============================================

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

    last12 = station_df[features].tail(12).values

    X = scaler_X.transform(last12)

    X = X.reshape(
        1,
        12,
        3
    )

    X = torch.tensor(
        X,
        dtype=torch.float32
    ).to(device)

    with torch.no_grad():

        pred = model(X)

    pred = pred.cpu().numpy()

    pred = scaler_y.inverse_transform(pred)[0]

    last = station_df.iloc[-1]

    results.append({

        "Station Code": station,
        "Station Name": last["Station Name"],
        "State": last["State"],

        "Forecast_Year": 2026,
        "Forecast_Month": 1,
        "Forecast_Round": 1,

        "Pred_DO": round(float(pred[0]),3),
        "Pred_pH": round(float(pred[1]),3),
        "Pred_BOD": round(float(pred[2]),3)

    })


forecast = pd.DataFrame(results)


print("\n")
print("="*50)
print("FORECAST")
print("="*50)

print(forecast.head())

print("\nStations :", len(forecast))


forecast.to_csv(

    DATA_FOLDER /
    "Forecast_Jan2026.csv",

    index=False

)


print("\nSaved Successfully")

print(
    DATA_FOLDER /
    "Forecast_Jan2026.csv"
)