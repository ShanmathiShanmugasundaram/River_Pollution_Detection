import numpy as np
import torch
from pathlib import Path
import joblib

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from itransformer_model import iTransformer

# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
MODEL_FOLDER = PROJECT_DIR / "models"

# ============================================
# Load Validation Data
# ============================================

X_val = np.load(DATA_FOLDER / "X_val_scaled.npy")
y_val = np.load(DATA_FOLDER / "y_val_scaled.npy")

print("=" * 50)
print("VALIDATION DATA")
print("=" * 50)

print("X_val :", X_val.shape)
print("y_val :", y_val.shape)

# ============================================
# Load Scaler
# ============================================

scaler_y = joblib.load(DATA_FOLDER / "scaler_y.pkl")

# ============================================
# Load Model
# ============================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = iTransformer().to(device)

model.load_state_dict(
    torch.load(
        MODEL_FOLDER / "best_itransformer.pth",
        map_location=device
    )
)

model.eval()

# ============================================
# Prediction
# ============================================

X_tensor = torch.tensor(
    X_val,
    dtype=torch.float32
).to(device)

with torch.no_grad():

    prediction_scaled = model(X_tensor)

prediction_scaled = prediction_scaled.cpu().numpy()

# ============================================
# Convert Back
# ============================================

prediction = scaler_y.inverse_transform(prediction_scaled)

actual = scaler_y.inverse_transform(y_val)

# ============================================
# Metrics
# ============================================

names = ["DO", "pH", "BOD"]

print()
print("=" * 50)
print("MODEL PERFORMANCE")
print("=" * 50)

for i in range(3):

    mae = mean_absolute_error(
        actual[:, i],
        prediction[:, i]
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual[:, i],
            prediction[:, i]
        )
    )

    r2 = r2_score(
        actual[:, i],
        prediction[:, i]
    )

    print(f"\n{names[i]}")

    print(f"MAE  : {mae:.4f}")

    print(f"RMSE : {rmse:.4f}")

    print(f"R²   : {r2:.4f}")

# ============================================
# Save Predictions
# ============================================

np.save(
    DATA_FOLDER / "prediction.npy",
    prediction
)

np.save(
    DATA_FOLDER / "actual.npy",
    actual
)

print()
print("=" * 50)
print("Saved Successfully")
print("=" * 50)

print(DATA_FOLDER / "prediction.npy")
print(DATA_FOLDER / "actual.npy")