import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
OUTPUT_FOLDER = PROJECT_DIR / "output"

OUTPUT_FOLDER.mkdir(exist_ok=True)

# ============================================
# Load Data
# ============================================

actual = np.load(DATA_FOLDER / "actual.npy")
prediction = np.load(DATA_FOLDER / "prediction.npy")

print("=" * 50)
print("DATA LOADED")
print("=" * 50)

print("Actual :", actual.shape)
print("Prediction :", prediction.shape)

# ============================================
# Parameter Names
# ============================================

parameters = ["DO", "pH", "BOD"]

# ============================================
# Plot
# ============================================

for i, parameter in enumerate(parameters):

    plt.figure(figsize=(12,5))

    plt.plot(
        actual[:, i],
        label="Actual",
        linewidth=2
    )

    plt.plot(
        prediction[:, i],
        label="Predicted",
        linewidth=2
    )

    plt.title(f"{parameter} Prediction")

    plt.xlabel("Validation Samples")

    plt.ylabel(parameter)

    plt.legend()

    plt.tight_layout()

    save_path = OUTPUT_FOLDER / f"{parameter}_Prediction.png"

    plt.savefig(save_path)

    plt.close()

    print(f"Saved : {save_path}")

print()
print("=" * 50)
print("ALL PLOTS SAVED")
print("=" * 50)