import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib
PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
X_train = np.load(DATA_FOLDER / "X_train.npy")
X_val = np.load(DATA_FOLDER / "X_val.npy")

y_train = np.load(DATA_FOLDER / "y_train.npy")
y_val = np.load(DATA_FOLDER / "y_val.npy")
print("=" * 50)
print("BEFORE SCALING")
print("=" * 50)

print("X_train :", X_train.shape)
print("X_val   :", X_val.shape)

print("y_train :", y_train.shape)
print("y_val   :", y_val.shape)
scaler_X = StandardScaler()

scaler_y = StandardScaler()
X_train_2D = X_train.reshape(-1, X_train.shape[-1])

X_val_2D = X_val.reshape(-1, X_val.shape[-1])
X_train_scaled = scaler_X.fit_transform(X_train_2D)

X_val_scaled = scaler_X.transform(X_val_2D)

X_train_scaled = X_train_scaled.reshape(X_train.shape)

X_val_scaled = X_val_scaled.reshape(X_val.shape)
y_train_scaled = scaler_y.fit_transform(y_train)

y_val_scaled = scaler_y.transform(y_val)
np.save(DATA_FOLDER / "X_train_scaled.npy", X_train_scaled)

np.save(DATA_FOLDER / "X_val_scaled.npy", X_val_scaled)

np.save(DATA_FOLDER / "y_train_scaled.npy", y_train_scaled)

np.save(DATA_FOLDER / "y_val_scaled.npy", y_val_scaled)
joblib.dump(
    scaler_X,
    DATA_FOLDER / "scaler_X.pkl"
)

joblib.dump(
    scaler_y,
    DATA_FOLDER / "scaler_y.pkl"
)
print()

print("=" * 50)
print("AFTER SCALING")
print("=" * 50)

print("X_train :", X_train_scaled.shape)

print("X_val :", X_val_scaled.shape)

print("y_train :", y_train_scaled.shape)

print("y_val :", y_val_scaled.shape)

print()


print("\nSaved Files")

print(DATA_FOLDER / "X_train_scaled.npy")
print(DATA_FOLDER / "X_val_scaled.npy")
print(DATA_FOLDER / "y_train_scaled.npy")
print(DATA_FOLDER / "y_val_scaled.npy")
print(DATA_FOLDER / "scaler_X.pkl")
print(DATA_FOLDER / "scaler_y.pkl")




print("Saved Successfully")

