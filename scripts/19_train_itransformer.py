import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path

# ============================================
# Import Model
# ============================================

from itransformer_model import iTransformer

# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
MODEL_FOLDER = PROJECT_DIR / "models"

MODEL_FOLDER.mkdir(exist_ok=True)

# ============================================
# Load Data
# ============================================

X_train = np.load(DATA_FOLDER / "X_train_scaled.npy")
X_val = np.load(DATA_FOLDER / "X_val_scaled.npy")

y_train = np.load(DATA_FOLDER / "y_train_scaled.npy")
y_val = np.load(DATA_FOLDER / "y_val_scaled.npy")

print("=" * 50)
print("DATA LOADED")
print("=" * 50)

print("X_train :", X_train.shape)
print("y_train :", y_train.shape)

print("X_val :", X_val.shape)
print("y_val :", y_val.shape)

# ============================================
# Convert to Torch
# ============================================

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)

X_val = torch.tensor(X_val, dtype=torch.float32)
y_val = torch.tensor(y_val, dtype=torch.float32)

# ============================================
# DataLoader
# ============================================

train_dataset = TensorDataset(X_train, y_train)
val_dataset = TensorDataset(X_val, y_val)

train_loader = DataLoader(
    train_dataset,
    batch_size=32,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=32,
    shuffle=False
)

# ============================================
# Device
# ============================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("\nUsing Device :", device)

# ============================================
# Model
# ============================================

model = iTransformer().to(device)

criterion = nn.MSELoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)

# ============================================
# Training
# ============================================

epochs = 50

best_val_loss = float("inf")

print("\nStarting Training...\n")

for epoch in range(epochs):

    # --------------------------
    # Training
    # --------------------------

    model.train()

    train_loss = 0

    for X_batch, y_batch in train_loader:

        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        optimizer.zero_grad()

        prediction = model(X_batch)

        loss = criterion(prediction, y_batch)

        loss.backward()

        optimizer.step()

        train_loss += loss.item()

    train_loss /= len(train_loader)

    # --------------------------
    # Validation
    # --------------------------

    model.eval()

    val_loss = 0

    with torch.no_grad():

        for X_batch, y_batch in val_loader:

            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            prediction = model(X_batch)

            loss = criterion(prediction, y_batch)

            val_loss += loss.item()

    val_loss /= len(val_loader)

    print(
        f"Epoch {epoch+1:02d}/{epochs} | "
        f"Train Loss = {train_loss:.5f} | "
        f"Validation Loss = {val_loss:.5f}"
    )

    # --------------------------
    # Save Best Model
    # --------------------------

    if val_loss < best_val_loss:

        best_val_loss = val_loss

        torch.save(
            model.state_dict(),
            MODEL_FOLDER / "best_itransformer.pth"
        )

        print("Best Model Saved")

print("\n")
print("=" * 50)
print("TRAINING COMPLETED")
print("=" * 50)

print("Best Validation Loss :", best_val_loss)