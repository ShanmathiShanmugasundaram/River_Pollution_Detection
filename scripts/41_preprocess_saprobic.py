import pandas as pd
import os
import re

# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_DIR = r"C:\Users\SHANMATHI S\Downloads\River_Water_Quality_Project"

INPUT_FILE = os.path.join(
    PROJECT_DIR,
    "Ganga_Dataset",
    "Saprobic",
    "NMCG Data Ganga Biomonitoring 2017-2025 (1).xlsx"
)

OUTPUT_DIR = os.path.join(PROJECT_DIR, "Processed_Data")
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "Saprobic_Score.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# READ EXCEL WITHOUT HEADER
# --------------------------------------------------

df = pd.read_excel(
    INPUT_FILE,
    sheet_name="Main stream",
    header=None
)

print("Original shape:", df.shape)

# --------------------------------------------------
# HEADER ROW
# --------------------------------------------------

# Row 2 contains:
# Locations | 2017-18 pre | 2017-18 post | ...

headers = df.iloc[1].tolist()

print("\nDetected headers:")
print(headers)


# --------------------------------------------------
# DATA STARTS FROM ROW 3
# --------------------------------------------------

data = df.iloc[2:].copy()

# First column = State
# Second column = Location

data = data.rename(
    columns={
        0: "State",
        1: "Location"
    }
)


# --------------------------------------------------
# CONVERT WIDE → LONG
# --------------------------------------------------

records = []

for _, row in data.iterrows():

    state = row["State"]
    location = row["Location"]

    # Skip rows without location
    if pd.isna(location):
        continue

    state = "" if pd.isna(state) else str(state).strip()
    location = str(location).strip()

    # Remove # and * annotations from location
    location = re.sub(r"[#*]+$", "", location).strip()

    # Forward-fill state
    if state == "":
        state = None

    # Examine every year/season column
    for col_index in range(2, len(headers)):

        column_name = headers[col_index]

        if pd.isna(column_name):
            continue

        column_name = str(column_name).strip()

        # Match formats such as:
        # 2017-18 pre
        # 2017-18 post
        # 2024-25 Pre
        # 2024-25 Post

        match = re.match(
            r"(\d{4}-\d{2})\s*(pre|post)",
            column_name,
            re.IGNORECASE
        )

        if not match:
            continue

        year = match.group(1)
        season = match.group(2).capitalize()

        value = row.iloc[col_index]

        # Skip blank
        if pd.isna(value):
            continue

        value_str = str(value).strip()

        # Skip annotation values
        if value_str in ["*", "**", "#", "##", "-", ""]:
            continue

        # Convert score to numeric
        try:
            score = float(value)
        except (ValueError, TypeError):
            continue

        records.append({
            "State": state,
            "Location": location,
            "Year": year,
            "Season": season,
            "Saprobic_Score": score
        })


# --------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------

clean_df = pd.DataFrame(records)


# --------------------------------------------------
# FORWARD FILL STATE
# --------------------------------------------------

if not clean_df.empty:
    clean_df["State"] = clean_df["State"].ffill()


# --------------------------------------------------
# SORT
# --------------------------------------------------

clean_df = clean_df.sort_values(
    by=["State", "Location", "Year", "Season"]
).reset_index(drop=True)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

clean_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\n--------------------------------------")
print("PREPROCESSING COMPLETED")
print("--------------------------------------")

print("\nClean shape:")
print(clean_df.shape)

print("\nColumns:")
print(clean_df.columns.tolist())

print("\nFirst 15 records:")
print(clean_df.head(15).to_string(index=False))

print("\nNumber of states:")
print(clean_df["State"].nunique())

print("\nNumber of locations:")
print(clean_df["Location"].nunique())

print("\nYears:")
print(clean_df["Year"].unique())

print("\nSeasons:")
print(clean_df["Season"].unique())

print("\nMissing values:")
print(clean_df.isnull().sum())

print("\nSaprobic score range:")
print(
    clean_df["Saprobic_Score"].min(),
    "to",
    clean_df["Saprobic_Score"].max()
)

print("\nSaved to:")
print(OUTPUT_FILE)