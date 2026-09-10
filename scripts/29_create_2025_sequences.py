import pandas as pd
import numpy as np
from pathlib import Path


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"


# ============================================
# Load Dataset
# ============================================

file = DATA_FOLDER / "Test_2025_Dataset.csv"

df = pd.read_csv(file)


print("="*50)
print("2025 DATA")
print("="*50)

print(df.shape)
print(df.head())


# ============================================
# Features
# ============================================

features = [
    "DO",
    "pH",
    "BOD"
]


sequence_length = 12


X = []
y = []


# ============================================
# Create Station-wise Sequence
# ============================================

for station, station_df in df.groupby("Station Code"):


    station_df = station_df.sort_values(
        by=[
            "Year",
            "Month_No",
            "Round"
        ]
    )


    values = station_df[features].values


    # Need minimum 13 values
    if len(values) <= sequence_length:
        continue


    for i in range(len(values)-sequence_length):

        X.append(
            values[i:i+sequence_length]
        )

        y.append(
            values[i+sequence_length]
        )



X = np.array(X)
y = np.array(y)



print("\n"+"="*50)
print("SEQUENCE DATA")
print("="*50)


print("X_test :", X.shape)
print("y_test :", y.shape)



# ============================================
# Save
# ============================================

np.save(
    DATA_FOLDER / "X_2025.npy",
    X
)

np.save(
    DATA_FOLDER / "y_2025.npy",
    y
)


print("\nSaved Successfully")

print(
    DATA_FOLDER / "X_2025.npy"
)

print(
    DATA_FOLDER / "y_2025.npy"
)