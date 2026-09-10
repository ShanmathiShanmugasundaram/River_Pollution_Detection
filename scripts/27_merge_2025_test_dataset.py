import pandas as pd
from pathlib import Path


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"


# ============================================
# Load datasets
# ============================================

print("=" * 50)
print("LOADING 2025 DATASETS")
print("=" * 50)


do_df = pd.read_csv(DATA_FOLDER / "DO_2025.csv")
ph_df = pd.read_csv(DATA_FOLDER / "PH_2025.csv")
bod_df = pd.read_csv(DATA_FOLDER / "BOD_2025.csv")


print("DO  :", do_df.shape)
print("pH  :", ph_df.shape)
print("BOD :", bod_df.shape)



# ============================================
# Merge DO + pH
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


print("\nMerging DO and pH...")


df = pd.merge(
    do_df,
    ph_df,
    on=merge_columns,
    how="inner"
)



# ============================================
# Merge BOD
# ============================================

print("Merging BOD...")


df = pd.merge(
    df,
    bod_df,
    on=merge_columns,
    how="inner"
)



# ============================================
# Select final columns
# ============================================

df = df[
    [
        "Year",
        "Month_No",
        "Month",
        "Round",
        "State",
        "Station Code",
        "Station Name",
        "DO",
        "pH",
        "BOD"
    ]
]


# ============================================
# Cleaning
# ============================================

df = df.dropna()


df["Year"] = df["Year"].astype(int)


# ============================================
# Output
# ============================================

print("\n" + "=" * 50)
print("FINAL 2025 TEST DATASET")
print("=" * 50)

print("Records :", len(df))
print("Stations :", df["Station Code"].nunique())

print(df.head())


output_file = DATA_FOLDER / "Test_2025_Dataset.csv"

df.to_csv(
    output_file,
    index=False
)


print("\nSaved Successfully")
print(output_file)