import pandas as pd
from pathlib import Path

# ==================================================
# Paths
# ==================================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"

# ==================================================
# Load Forecast
# ==================================================

df = pd.read_csv(
    DATA_FOLDER / "Forecast_2026.csv"
)

print("=" * 50)
print("2026 FORECAST")
print("=" * 50)

print(df.shape)
print(df.head())

# ==================================================
# WQI Calculation
# ==================================================

def calculate_wqi(do, ph, bod):

    # DO Score (higher is better)
    do_score = min((do / 10.0) * 100, 100)

    # pH Score (ideal = 7)
    ph_score = max(0, 100 - abs(ph - 7) * 25)

    # BOD Score (lower is better)
    bod_score = max(0, 100 - (bod * 15))

    wqi = (
        0.40 * do_score +
        0.30 * ph_score +
        0.30 * bod_score
    )

    return round(wqi, 2)

# ==================================================
# Compute WQI
# ==================================================

df["Predicted_WQI"] = df.apply(
    lambda x: calculate_wqi(
        x["Pred_DO"],
        x["Pred_pH"],
        x["Pred_BOD"]
    ),
    axis=1
)

# ==================================================
# Category
# ==================================================

def category(wqi):

    if wqi >= 90:
        return "Excellent"

    elif wqi >= 70:
        return "Good"

    elif wqi >= 50:
        return "Medium"

    else:
        return "Poor"

df["Category"] = df["Predicted_WQI"].apply(category)

# ==================================================
# Statistics
# ==================================================

print("\n")
print("=" * 50)
print("WQI STATISTICS")
print("=" * 50)

print(df["Predicted_WQI"].describe())

print("\nCategories")

print(df["Category"].value_counts())

# ==================================================
# Save
# ==================================================

output = DATA_FOLDER / "Forecast_2026_WQI.csv"

df.to_csv(output, index=False)

print("\nSaved Successfully")

print(output)