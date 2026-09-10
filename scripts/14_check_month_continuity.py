import pandas as pd
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent

file = PROJECT_DIR / "Processed_Data" / "Filtered_Water_Quality_Dataset.csv"

df = pd.read_csv(file)


print("==============================")
print("MONTH CONTINUITY CHECK")
print("==============================")


df["Date"] = pd.to_datetime(
    dict(
        year=df["Year"],
        month=df["Month_No"],
        day=1
    )
)


missing_summary = {}


for station, data in df.groupby("Station Code"):

    data = data.sort_values("Date")

    full_range = pd.date_range(
        start=data["Date"].min(),
        end=data["Date"].max(),
        freq="MS"
    )

    missing_months = len(
        full_range.difference(data["Date"])
    )

    missing_summary[station] = missing_months


result = pd.Series(missing_summary)


print(result.describe())


print("\nStations with missing months:")

print(
    result[result > 0]
)