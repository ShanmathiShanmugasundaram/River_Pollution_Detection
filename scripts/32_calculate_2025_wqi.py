import numpy as np
import pandas as pd
from pathlib import Path


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"


# ============================================
# Load Data
# ============================================

actual = np.load(
    DATA_FOLDER / "actual_2025.npy"
)

prediction = np.load(
    DATA_FOLDER / "prediction_2025.npy"
)


print("="*50)
print("2025 WQI CALCULATION")
print("="*50)

print("Actual :", actual.shape)
print("Prediction :", prediction.shape)



# ============================================
# Modified WQI Formula
# ============================================

def calculate_wqi(data):

    DO = data[:,0]
    pH = data[:,1]
    BOD = data[:,2]


    # DO score
    do_score = (
        DO / 8.0
    ) * 100


    # pH score
    ph_score = (
        1 - abs(pH - 7) / 7
    ) * 100


    # BOD score
    bod_score = (
        100 - (BOD / 5.0)*100
    )


    # Weighted WQI

    WQI = (
        0.4 * do_score +
        0.3 * ph_score +
        0.3 * bod_score
    )


    # Limit range

    WQI = np.clip(
        WQI,
        0,
        100
    )


    return WQI



# ============================================
# Calculate
# ============================================

actual_wqi = calculate_wqi(actual)

predicted_wqi = calculate_wqi(prediction)



print("\n")
print("="*50)
print("WQI CREATED")
print("="*50)

print("Samples :", len(actual_wqi))



# ============================================
# Category
# ============================================

def category(wqi):

    if wqi >= 90:
        return "Excellent"

    elif wqi >= 70:
        return "Good"

    elif wqi >= 50:
        return "Medium"

    elif wqi >= 25:
        return "Poor"

    else:
        return "Very Poor"



# ============================================
# Save CSV
# ============================================

df = pd.DataFrame({

    "Actual_DO": actual[:,0],
    "Actual_pH": actual[:,1],
    "Actual_BOD": actual[:,2],

    "Predicted_DO": prediction[:,0],
    "Predicted_pH": prediction[:,1],
    "Predicted_BOD": prediction[:,2],

    "Actual_WQI": actual_wqi,
    "Predicted_WQI": predicted_wqi,

    "Actual_Category":
        [category(x) for x in actual_wqi],

    "Predicted_Category":
        [category(x) for x in predicted_wqi]

})


# save numpy

np.save(
    DATA_FOLDER / "actual_wqi_2025.npy",
    actual_wqi
)


np.save(
    DATA_FOLDER / "predicted_wqi_2025.npy",
    predicted_wqi
)



df.to_csv(
    DATA_FOLDER / "wqi_results_2025.csv",
    index=False
)



print("\nSaved Successfully")

print(
    DATA_FOLDER / "actual_wqi_2025.npy"
)

print(
    DATA_FOLDER / "predicted_wqi_2025.npy"
)

print(
    DATA_FOLDER / "wqi_results_2025.csv"
)