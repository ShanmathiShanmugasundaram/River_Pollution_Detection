import pandas as pd

# ============================================================
# 2026 HOTSPOT ANALYSIS
# CPCB Class B criteria:
# DO  >= 5 mg/L
# BOD <= 3 mg/L
# pH  = 6.5 to 8.5
# ============================================================

input_file = r"Processed_Data\Forecast_2026_WQI.csv"
output_file = r"Processed_Data\Hotspot_Analysis_2026.csv"

# ------------------------------------------------------------
# 1. Load 2026 forecast + WQI data
# ------------------------------------------------------------
df = pd.read_csv(input_file)

# ------------------------------------------------------------
# 2. CPCB criterion checks
# ------------------------------------------------------------

# BOD criterion exceeded
df["BOD_Exceed"] = df["Pred_BOD"] > 3

# DO criterion violated
df["DO_Violation"] = df["Pred_DO"] < 5

# pH criterion violated
df["pH_Violation"] = (
    (df["Pred_pH"] < 6.5) |
    (df["Pred_pH"] > 8.5)
)

# Any CPCB criterion violated
df["Any_CPCB_Violation"] = (
    df["BOD_Exceed"] |
    df["DO_Violation"] |
    df["pH_Violation"]
)

# ------------------------------------------------------------
# 3. Station-level aggregation
# ------------------------------------------------------------
x = df.groupby(
    ["Station Code", "Station Name", "State"]
).agg(
    Forecast_Months=("Pred_WQI", "count"),

    Mean_WQI=("Pred_WQI", "mean"),
    Min_WQI=("Pred_WQI", "min"),

    Mean_DO=("Pred_DO", "mean"),
    Min_DO=("Pred_DO", "min"),

    Mean_pH=("Pred_pH", "mean"),
    Min_pH=("Pred_pH", "min"),
    Max_pH=("Pred_pH", "max"),

    Mean_BOD=("Pred_BOD", "mean"),
    Max_BOD=("Pred_BOD", "max"),

    BOD_Exceed_Months=("BOD_Exceed", "sum"),
    DO_Violation_Months=("DO_Violation", "sum"),
    pH_Violation_Months=("pH_Violation", "sum"),

    Any_CPCB_Violation_Months=("Any_CPCB_Violation", "sum")
).reset_index()

# ------------------------------------------------------------
# 4. Calculate percentages
# ------------------------------------------------------------

x["BOD_Exceed_Percent"] = (
    x["BOD_Exceed_Months"] /
    x["Forecast_Months"] * 100
)

x["DO_Violation_Percent"] = (
    x["DO_Violation_Months"] /
    x["Forecast_Months"] * 100
)

x["pH_Violation_Percent"] = (
    x["pH_Violation_Months"] /
    x["Forecast_Months"] * 100
)

x["CPCB_Violation_Percent"] = (
    x["Any_CPCB_Violation_Months"] /
    x["Forecast_Months"] * 100
)

# ------------------------------------------------------------
# 5. Project analytical hotspot level
#
# NOTE:
# These labels are NOT CPCB regulatory classifications.
# They are project-defined based on predicted WQI and
# persistence of CPCB criterion exceedance.
# ------------------------------------------------------------

def hotspot_level(row):

    wqi = row["Mean_WQI"]
    violation = row["CPCB_Violation_Percent"]

    # Strong persistent predicted hotspot
    if wqi < 85 and violation >= 75:
        return "High Hotspot"

    # Recurring predicted hotspot
    elif wqi < 90 and violation >= 25:
        return "Moderate Hotspot"

    # Otherwise
    else:
        return "Low / No Hotspot"


x["Hotspot_Level"] = x.apply(hotspot_level, axis=1)

# ------------------------------------------------------------
# 6. Sort strongest hotspots first
# ------------------------------------------------------------

x = x.sort_values(
    ["Hotspot_Level", "Mean_WQI", "CPCB_Violation_Percent"],
    ascending=[True, True, False]
)

# ------------------------------------------------------------
# 7. Round numerical values
# ------------------------------------------------------------

numeric_columns = [
    "Mean_WQI",
    "Min_WQI",
    "Mean_DO",
    "Min_DO",
    "Mean_pH",
    "Min_pH",
    "Max_pH",
    "Mean_BOD",
    "Max_BOD",
    "BOD_Exceed_Percent",
    "DO_Violation_Percent",
    "pH_Violation_Percent",
    "CPCB_Violation_Percent"
]

x[numeric_columns] = x[numeric_columns].round(2)

# ------------------------------------------------------------
# 8. Save
# ------------------------------------------------------------

x.to_csv(output_file, index=False)

# ------------------------------------------------------------
# 9. Display results
# ------------------------------------------------------------

print("\n==============================================")
print("2026 HOTSPOT ANALYSIS COMPLETED")
print("==============================================")

print("Input shape :", df.shape)
print("Output shape:", x.shape)

print("\nHotspot distribution:")
print(x["Hotspot_Level"].value_counts())

print("\nTop predicted hotspots:")
print(
    x[
        [
            "Station Code",
            "Station Name",
            "State",
            "Mean_WQI",
            "BOD_Exceed_Months",
            "BOD_Exceed_Percent",
            "DO_Violation_Months",
            "pH_Violation_Months",
            "CPCB_Violation_Percent",
            "Mean_BOD",
            "Hotspot_Level"
        ]
    ].head(20).to_string(index=False)
)

print("\nSaved to:")
print(output_file)