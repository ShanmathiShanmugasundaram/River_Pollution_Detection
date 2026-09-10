import pandas as pd

# ============================================================
# 2026 PREDICTED WQI CALCULATION
# Uses the SAME WQI methodology as script 22
# ============================================================

input_file = r"Processed_Data\Forecast_2026.csv"
output_file = r"Processed_Data\Forecast_2026_WQI.csv"


# -----------------------------
# WQI scoring functions
# -----------------------------

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


def calculate_wqi(do, ph, bod):
    return (
        0.4 * score_do(do)
        + 0.3 * score_ph(ph)
        + 0.3 * score_bod(bod)
    )


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


# -----------------------------
# Load 2026 predictions
# -----------------------------

df = pd.read_csv(input_file)

print("Input shape:", df.shape)

# -----------------------------
# Calculate predicted WQI
# -----------------------------

df["Pred_WQI"] = df.apply(
    lambda row: calculate_wqi(
        row["Pred_DO"],
        row["Pred_pH"],
        row["Pred_BOD"]
    ),
    axis=1
)

df["Predicted_Class"] = df["Pred_WQI"].apply(classify)


# -----------------------------
# Save
# -----------------------------

df.to_csv(output_file, index=False)

print("\n2026 PREDICTED WQI CALCULATION COMPLETED")
print("Output shape:", df.shape)
print("Saved to:", output_file)

print("\nPredicted WQI statistics:")
print(df["Pred_WQI"].describe().round(2))

print("\nPredicted quality class distribution:")
print(df["Predicted_Class"].value_counts())

print("\nTop 15 stations by predicted WQI:")
print(
    df.groupby(["Station Code", "Station Name"])["Pred_WQI"]
    .mean()
    .sort_values()
    .head(15)
    .round(2)
)