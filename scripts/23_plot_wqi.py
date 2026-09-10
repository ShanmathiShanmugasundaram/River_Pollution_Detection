import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# PATHS
# ==========================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
OUTPUT_FOLDER = PROJECT_DIR / "output"

OUTPUT_FOLDER.mkdir(exist_ok=True)

# ==========================================
# LOAD DATA
# ==========================================

actual = np.load(DATA_FOLDER / "actual_wqi.npy")
predicted = np.load(DATA_FOLDER / "predicted_wqi.npy")

print("=" * 50)
print("DATA LOADED")
print("=" * 50)

print("Actual :", actual.shape)
print("Prediction :", predicted.shape)

# ==========================================
# PLOT
# ==========================================

plt.figure(figsize=(14,6))

plt.plot(actual[:200],
         label="Actual WQI",
         linewidth=2)

plt.plot(predicted[:200],
         label="Predicted WQI",
         linewidth=2)

plt.xlabel("Samples")

plt.ylabel("Modified WQI")

plt.title("Actual vs Predicted Water Quality Index")

plt.legend()

plt.grid(True)

save_path = OUTPUT_FOLDER / "WQI_Prediction.png"

plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print("Saved :", save_path)