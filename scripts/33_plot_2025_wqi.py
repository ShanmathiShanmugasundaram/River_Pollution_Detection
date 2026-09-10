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
# Load WQI
# ============================================

actual_wqi = np.load(
    DATA_FOLDER / "actual_wqi_2025.npy"
)

predicted_wqi = np.load(
    DATA_FOLDER / "predicted_wqi_2025.npy"
)



print("="*50)
print("2025 WQI PLOT")
print("="*50)

print("Actual :", actual_wqi.shape)
print("Prediction :", predicted_wqi.shape)



# ============================================
# Plot
# ============================================

plt.figure(figsize=(12,5))


plt.plot(
    actual_wqi[:200],
    label="Actual WQI"
)


plt.plot(
    predicted_wqi[:200],
    label="Predicted WQI"
)


plt.xlabel(
    "Samples"
)

plt.ylabel(
    "Water Quality Index"
)


plt.title(
    "2025 Actual vs Predicted WQI"
)


plt.legend()

plt.grid(True)



save_path = (
    OUTPUT_FOLDER /
    "WQI_2025_Prediction.png"
)


plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)


plt.close()



print("\nSaved:")
print(save_path)