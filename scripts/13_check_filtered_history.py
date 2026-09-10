import pandas as pd
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent

file = PROJECT_DIR / "Processed_Data" / "Filtered_Water_Quality_Dataset.csv"


df = pd.read_csv(file)


print("==============================")
print("FILTERED STATION HISTORY")
print("==============================")


history = (
    df.groupby("Station Code")["Year"]
    .nunique()
)


print(history.describe())


print("\nMinimum Years:")
print(history.min())


print("\nMaximum Years:")
print(history.max())