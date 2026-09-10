import numpy as np
import pandas as pd
from pathlib import Path

# ==================================================
# PATHS
# ==================================================

PROJECT_DIR = Path(__file__).parent.parent
DATA_FOLDER = PROJECT_DIR / "Processed_Data"

# ==================================================
# LOAD DATA
# ==================================================

actual = np.load(DATA_FOLDER / "actual.npy")
prediction = np.load(DATA_FOLDER / "prediction.npy")

print("=" * 50)
print("DATA LOADED")
print("=" * 50)
print("Actual     :", actual.shape)
print("Prediction :", prediction.shape)


# ==================================================
# PARAMETER SCORING
# ==================================================

def score_do(value):
    if value >= 8:
        return 100
    elif value >= 6:
        return 80
    elif value >= 4:
        return 60
    elif value >= 2:
        return 40
    else:
        return 20


def score_ph(value):
    if 6.5 <= value <= 8.5:
        return 100
    elif (6.0 <= value < 6.5) or (8.5 < value <= 9.0):
        return 80
    elif (5.5 <= value < 6.0) or (9.0 < value <= 9.5):
        return 60
    else:
        return 40


def score_bod(value):
    if value <= 2:
        return 100
    elif value <= 3:
        return 80
    elif value <= 5:
        return 60
    elif value <= 8:
        return 40
    else:
        return 20


# ==================================================
# WQI CALCULATION
# ==================================================

def calculate_wqi(do, ph, bod):

    do_score = score_do(do)
    ph_score = score_ph(ph)
    bod_score = score_bod(bod)

    wqi = (
        0.4 * do_score +
        0.3 * ph_score +
        0.3 * bod_score
    )

    return wqi


# ==================================================
# CLASSIFICATION
# ==================================================

def classify(wqi):

    if wqi >= 90:
        return "Excellent"

    elif wqi >= 70:
        return "Good"

    elif wqi >= 50:
        return "Moderate"

    elif wqi >= 25:
        return "Poor"

    else:
        return "Very Poor"


# ==================================================
# CALCULATE WQI
# ==================================================

actual_wqi = []
predicted_wqi = []

actual_class = []
predicted_class = []

for a, p in zip(actual, prediction):

    actual_value = calculate_wqi(a[0], a[1], a[2])
    predicted_value = calculate_wqi(p[0], p[1], p[2])

    actual_wqi.append(actual_value)
    predicted_wqi.append(predicted_value)

    actual_class.append(classify(actual_value))
    predicted_class.append(classify(predicted_value))


actual_wqi = np.array(actual_wqi)
predicted_wqi = np.array(predicted_wqi)


# ==================================================
# SAVE
# ==================================================

np.save(DATA_FOLDER / "actual_wqi.npy", actual_wqi)
np.save(DATA_FOLDER / "predicted_wqi.npy", predicted_wqi)

results = pd.DataFrame({

    "Actual_DO": actual[:,0],
    "Actual_pH": actual[:,1],
    "Actual_BOD": actual[:,2],

    "Pred_DO": prediction[:,0],
    "Pred_pH": prediction[:,1],
    "Pred_BOD": prediction[:,2],

    "Actual_WQI": actual_wqi,
    "Predicted_WQI": predicted_wqi,

    "Actual_Class": actual_class,
    "Predicted_Class": predicted_class

})

results.to_csv(
    DATA_FOLDER / "wqi_results.csv",
    index=False
)

print()
print("=" * 50)
print("WQI CREATED")
print("=" * 50)

print("Samples :", len(results))

print()
print("Saved Files")

print(DATA_FOLDER / "actual_wqi.npy")
print(DATA_FOLDER / "predicted_wqi.npy")
print(DATA_FOLDER / "wqi_results.csv")