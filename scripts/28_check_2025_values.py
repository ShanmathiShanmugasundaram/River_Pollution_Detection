import pandas as pd
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent

file = PROJECT_DIR / "Processed_Data" / "Test_2025_Dataset.csv"

df = pd.read_csv(file)


print("="*50)
print("2025 VALUE CHECK")
print("="*50)


print("\nDO Statistics")
print(df["DO"].describe())


print("\npH Statistics")
print(df["pH"].describe())


print("\nBOD Statistics")
print(df["BOD"].describe())


print("\nUnique pH values")
print(df["pH"].unique()[:20])