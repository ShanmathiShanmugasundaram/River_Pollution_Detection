import pandas as pd
import numpy as np
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"



# ============================================
# Load Results
# ============================================

df = pd.read_csv(
    DATA_FOLDER / "wqi_results_2025.csv"
)


print("="*60)
print("FINAL WATER QUALITY ANALYSIS - 2025")
print("="*60)



# ============================================
# Dataset
# ============================================

print("\nDataset Samples :", len(df))



# ============================================
# WQI Statistics
# ============================================

print("\n==============================")
print("WQI STATISTICS")
print("==============================")


print("\nActual WQI")

print(
    df["Actual_WQI"].describe()
)


print("\nPredicted WQI")

print(
    df["Predicted_WQI"].describe()
)



# ============================================
# Category Distribution
# ============================================

print("\n==============================")
print("ACTUAL CATEGORY")
print("==============================")


print(
    df["Actual_Category"]
    .value_counts()
)



print("\n==============================")
print("PREDICTED CATEGORY")
print("==============================")


print(
    df["Predicted_Category"]
    .value_counts()
)



# ============================================
# Average Error
# ============================================

error = abs(
    df["Actual_WQI"] -
    df["Predicted_WQI"]
)


print("\n==============================")
print("WQI ERROR")
print("==============================")


print(
    "Mean Absolute WQI Error :",
    round(error.mean(),4)
)


print(
    "Maximum Error :",
    round(error.max(),4)
)



print("\nAnalysis Completed")