import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"

OUTPUT_FOLDER = PROJECT_DIR / "output"
OUTPUT_FOLDER.mkdir(exist_ok=True)


# ============================================
# Load Data
# ============================================

actual_2025 = pd.read_csv(
    DATA_FOLDER / "wqi_results_2025.csv"
)

forecast_2026 = pd.read_csv(
    DATA_FOLDER / "Forecast_2026_WQI.csv"
)


print("=" * 60)
print("2025 vs 2026 COMPARISON")
print("=" * 60)

print("2025 :", actual_2025.shape)
print("2026 :", forecast_2026.shape)


# ============================================
# Average Values
# ============================================

comparison = pd.DataFrame({

    "Parameter": ["DO", "pH", "BOD", "WQI"],

    "2025 Actual": [

        actual_2025["Actual_DO"].mean(),
        actual_2025["Actual_pH"].mean(),
        actual_2025["Actual_BOD"].mean(),
        actual_2025["Actual_WQI"].mean()

    ],

    "2026 Forecast": [

        forecast_2026["Pred_DO"].mean(),
        forecast_2026["Pred_pH"].mean(),
        forecast_2026["Pred_BOD"].mean(),
        forecast_2026["Predicted_WQI"].mean()

    ]

})


print("\n")
print(comparison.round(3))


# ============================================
# Save Comparison Table
# ============================================

comparison.to_csv(
    DATA_FOLDER / "Comparison_2025_2026.csv",
    index=False
)


# ============================================
# Plot Comparison
# ============================================

for parameter in comparison["Parameter"]:

    row = comparison[
        comparison["Parameter"] == parameter
    ]

    values = [

        row["2025 Actual"].values[0],
        row["2026 Forecast"].values[0]

    ]

    plt.figure(figsize=(5,5))

    plt.bar(

        ["2025", "2026"],
        values

    )

    plt.ylabel(parameter)

    plt.title(f"{parameter}: 2025 vs 2026")

    plt.tight_layout()

    plt.savefig(

        OUTPUT_FOLDER /
        f"{parameter}_Comparison.png"

    )

    plt.close()


# ============================================
# WQI Category Comparison
# ============================================

actual_category = (
    actual_2025["Actual_Category"]
    .value_counts()
)

forecast_category = (
    forecast_2026["Category"]
    .value_counts()
)


category_df = pd.DataFrame({

    "2025": actual_category,

    "2026": forecast_category

}).fillna(0)


category_df.plot(

    kind="bar",
    figsize=(8,5)

)

plt.ylabel("Samples")

plt.title("Water Quality Category Comparison")

plt.tight_layout()

plt.savefig(

    OUTPUT_FOLDER /
    "Category_Comparison.png"

)

plt.close()


# ============================================
# Final Conclusion
# ============================================

print("\n")
print("=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Average WQI (2025): {comparison.iloc[3,1]:.2f}")

print(f"Average WQI (2026): {comparison.iloc[3,2]:.2f}")


if comparison.iloc[3,2] > comparison.iloc[3,1]:

    print("\nPrediction:")
    print("Water quality is expected to improve in 2026.")

elif comparison.iloc[3,2] < comparison.iloc[3,1]:

    print("\nPrediction:")
    print("Water quality is expected to decline slightly in 2026.")

else:

    print("\nPrediction:")
    print("Water quality is expected to remain stable.")


print("\nSaved Successfully")

print(DATA_FOLDER / "Comparison_2025_2026.csv")

print(OUTPUT_FOLDER)