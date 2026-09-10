import numpy as np
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
# Load 2025 Data
# ============================================

X_test = np.load(
    DATA_FOLDER / "X_2025.npy"
)

y_test = np.load(
    DATA_FOLDER / "y_2025.npy"
)


print("="*50)
print("2025 TEST DATA")
print("="*50)

print("X_test :", X_test.shape)
print("y_test :", y_test.shape)



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
# Scale Input
# ============================================

samples, seq, features = X_test.shape


X_scaled = scaler_X.transform(
    X_test.reshape(-1, features)
)


X_scaled = X_scaled.reshape(
    samples,
    seq,
    features
)



# ============================================
# Convert Tensor
# ============================================

X_tensor = torch.tensor(
    X_scaled,
    dtype=torch.float32
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



print("\n")
print("="*50)
print("MODEL LOADED")
print("="*50)



# ============================================
# Prediction
# ============================================

with torch.no_grad():

    X_tensor = X_tensor.to(device)

    prediction = model(
        X_tensor
    )


prediction = prediction.cpu().numpy()



# ============================================
# Inverse Scaling
# ============================================

prediction_original = scaler_y.inverse_transform(
    prediction
)


actual_original = y_test



print("\n")
print("="*50)
print("PREDICTION RESULT")
print("="*50)


print("Prediction shape :", prediction_original.shape)
print("Actual shape     :", actual_original.shape)


print("\nFirst 5 Predictions")
print(prediction_original[:5])


print("\nFirst 5 Actual")
print(actual_original[:5])



# ============================================
# Save
# ============================================

np.save(
    DATA_FOLDER / "prediction_2025.npy",
    prediction_original
)


np.save(
    DATA_FOLDER / "actual_2025.npy",
    actual_original
)


print("\nSaved Successfully")

print(
    DATA_FOLDER / "prediction_2025.npy"
)

print(
    DATA_FOLDER / "actual_2025.npy"
)