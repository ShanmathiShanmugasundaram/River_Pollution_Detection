import pandas as pd
import numpy as np
from pathlib import Path

# ==================================================
# PATHS
# ==================================================

PROJECT_DIR = Path(__file__).parent.parent
DATA_FOLDER = PROJECT_DIR / "Processed_Data"

chemical_file = DATA_FOLDER / "Final_Water_Quality_Dataset.csv"
saprobic_file = DATA_FOLDER / "Saprobic_Score_Classified.csv"
mapping_file = DATA_FOLDER / "Saprobic_Station_Mapping.csv"

output_file = DATA_FOLDER / "Seasonal_WQI_Saprobic_Validation.csv"


# ==================================================
# LOAD DATA
# ==================================================

chemical = pd.read_csv(chemical_file)
saprobic = pd.read_csv(saprobic_file)
mapping = pd.read_csv(mapping_file)

print("=" * 60)
print("DATA LOADED")
print("=" * 60)

print("Chemical data :", chemical.shape)
print("Saprobic data :", saprobic.shape)
print("Station mapping :", mapping.shape)


# ==================================================
# CLEAN NUMERIC CHEMICAL VALUES
# ==================================================

# BDL values such as "1 (BDL)" become NaN
chemical["DO"] = pd.to_numeric(chemical["DO"], errors="coerce")
chemical["pH"] = pd.to_numeric(chemical["pH"], errors="coerce")
chemical["BOD"] = pd.to_numeric(chemical["BOD"], errors="coerce")


# ==================================================
# WQI SCORING
# Same methodology as script 22
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


def calculate_wqi(do, ph, bod):

    return (
        0.4 * score_do(do)
        + 0.3 * score_ph(ph)
        + 0.3 * score_bod(bod)
    )


def classify_wqi(wqi):

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
# CALCULATE WQI FOR EACH CHEMICAL RECORD
# ==================================================

chemical["WQI"] = np.nan

valid = chemical[["DO", "pH", "BOD"]].notna().all(axis=1)

chemical.loc[valid, "WQI"] = chemical.loc[valid].apply(
    lambda row: calculate_wqi(
        row["DO"],
        row["pH"],
        row["BOD"]
    ),
    axis=1
)


# ==================================================
# CREATE SEASONAL YEAR AND SEASON
# ==================================================

def get_season(month_no):

    if month_no in [3, 4, 5]:
        return "Pre"

    elif month_no in [10, 11, 12]:
        return "Post"

    return np.nan


chemical["Season"] = chemical["Month_No"].apply(get_season)

chemical = chemical.dropna(subset=["Season"])


# ==================================================
# SAPROBIC ACADEMIC-YEAR ALIGNMENT
#
# 2017-18 Post -> Oct-Dec 2017
# 2017-18 Pre  -> Mar-May 2018
#
# 2024-25 Post -> Oct-Dec 2024
# 2024-25 Pre  -> Mar-May 2025
# ==================================================

def saprobic_year(year, season):

    if season == "Post":
        return f"{year}-{str(year + 1)[-2:]}"

    elif season == "Pre":
        return f"{year - 1}-{str(year)[-2:]}"

    return np.nan


chemical["Saprobic_Year"] = chemical.apply(
    lambda row: saprobic_year(
        int(row["Year"]),
        row["Season"]
    ),
    axis=1
)


# ==================================================
# KEEP ONLY MAPPED STATIONS
# ==================================================

mapping["Station_Code"] = pd.to_numeric(
    mapping["Station_Code"],
    errors="coerce"
)

chemical["Station Code"] = pd.to_numeric(
    chemical["Station Code"],
    errors="coerce"
)

chemical = chemical[
    chemical["Station Code"].isin(mapping["Station_Code"])
]


# ==================================================
# SEASONAL CHEMICAL WQI
# ==================================================

seasonal = (
    chemical
    .groupby(
        ["Station Code", "Saprobic_Year", "Season"],
        as_index=False
    )
    .agg(
        Chemical_WQI=("WQI", "mean"),
        Chemical_Records=("WQI", "count"),
        Mean_DO=("DO", "mean"),
        Mean_pH=("pH", "mean"),
        Mean_BOD=("BOD", "mean")
    )
)


# ==================================================
# ADD WQI CLASS
# ==================================================

seasonal["Chemical_Quality"] = seasonal["Chemical_WQI"].apply(
    lambda x: classify_wqi(x) if pd.notna(x) else "Unknown"
)


# ==================================================
# MERGE STATION LOCATION
# ==================================================

seasonal = seasonal.merge(
    mapping,
    left_on="Station Code",
    right_on="Station_Code",
    how="left"
)


# ==================================================
# MERGE WITH SAPROBIC DATA
# ==================================================

validation = saprobic.merge(
    seasonal,
    left_on=[
        "Location",
        "Year",
        "Season"
    ],
    right_on=[
        "Saprobic_Location",
        "Saprobic_Year",
        "Season"
    ],
    how="inner"
)


# ==================================================
# FINAL COLUMNS
# ==================================================

validation = validation[
    [
        "State",
        "Location",
        "Station_Code",
        "Year",
        "Season",
        "Saprobic_Score",
        "Biological_Quality",
        "Chemical_WQI",
        "Chemical_Quality",
        "Chemical_Records",
        "Mean_DO",
        "Mean_pH",
        "Mean_BOD"
    ]
]


# ==================================================
# SAVE
# ==================================================

validation.to_csv(
    output_file,
    index=False
)


# ==================================================
# SUMMARY
# ==================================================

print()
print("=" * 60)
print("SEASONAL WQI + SAPROBIC VALIDATION CREATED")
print("=" * 60)

print("Validation shape :", validation.shape)

print()
print("Stations :", validation["Station_Code"].nunique())

print()
print("Biological Quality:")
print(validation["Biological_Quality"].value_counts())

print()
print("Chemical Quality:")
print(validation["Chemical_Quality"].value_counts())

print()
print("Season:")
print(validation["Season"].value_counts())

print()
print("Saved to:")
print(output_file)

print()
print("Preview:")
print(validation.head(15).to_string(index=False))