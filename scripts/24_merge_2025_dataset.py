import pandas as pd
from pathlib import Path

# ============================================
# PATHS
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATASET_FOLDER = PROJECT_DIR / "Ganga_Dataset"

PROCESSED_FOLDER = PROJECT_DIR / "Processed_Data"

# ============================================
# READ CSV FILES
# ============================================

do_df = pd.read_csv(PROCESSED_FOLDER / "Master_DO.csv")

ph_df = pd.read_csv(PROCESSED_FOLDER / "Master_PH.csv")

bod_df = pd.read_csv(PROCESSED_FOLDER / "Master_BOD.csv")

# ============================================
# KEEP ONLY 2025
# ============================================

do_df = do_df[do_df["Year"] == 2025]

ph_df = ph_df[ph_df["Year"] == 2025]

bod_df = bod_df[bod_df["Year"] == 2025]

print("=" * 50)
print("2025 RECORDS")
print("=" * 50)

print("DO :", len(do_df))
print("pH :", len(ph_df))
print("BOD:", len(bod_df))

# ============================================
# MERGE
# ============================================

merge_columns = [
    "Year",
    "Month_No",
    "Month",
    "Round",
    "State",
    "Station Code",
    "Station Name"
]

merged = do_df.merge(
    ph_df,
    on=merge_columns
)

merged = merged.merge(
    bod_df,
    on=merge_columns
)

print()
print("=" * 50)
print("FINAL TEST DATASET")
print("=" * 50)

print(merged.shape)

print()

print(merged.head())

# ============================================
# SAVE
# ============================================

save_path = PROCESSED_FOLDER / "Test_2025_Dataset.csv"

merged.to_csv(
    save_path,
    index=False
)

print()
print("Saved Successfully")
print(save_path)