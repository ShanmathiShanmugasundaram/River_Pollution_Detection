import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==================================================
# Paths
# ==================================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"
OUTPUT_FOLDER = PROJECT_DIR / "output"

OUTPUT_FOLDER.mkdir(exist_ok=True)

# ==================================================
# Load Forecast WQI Dataset
# ==================================================

df = pd.read_csv(
    DATA_FOLDER / "Forecast_2026_WQI.csv"
)

print("=" * 50)
print("2026 FORECAST DATA")
print("=" * 50)

print(df.shape)

# ==================================================
# Monthly Average
# ==================================================

monthly = (
    df.groupby(
        ["Forecast_Month_No", "Forecast_Month"]
    )
    .agg(
        {
            "Pred_DO": "mean",
            "Pred_pH": "mean",
            "Pred_BOD": "mean",
            "Predicted_WQI": "mean",
        }
    )
    .reset_index()
    .sort_values("Forecast_Month_No")
)

print("\nMonthly Average")
print(monthly)

months = monthly["Forecast_Month"]

# ==================================================
# DO
# ==================================================

plt.figure(figsize=(10,5))

plt.plot(
    months,
    monthly["Pred_DO"],
    marker="o",
    linewidth=2
)

plt.title("2026 Forecast - Average Dissolved Oxygen (DO)")
plt.xlabel("Month")
plt.ylabel("DO (mg/L)")
plt.grid(True)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "Forecast2026_DO.png",
    dpi=300
)

plt.close()

# ==================================================
# pH
# ==================================================

plt.figure(figsize=(10,5))

plt.plot(
    months,
    monthly["Pred_pH"],
    marker="o",
    linewidth=2
)

plt.title("2026 Forecast - Average pH")
plt.xlabel("Month")
plt.ylabel("pH")
plt.grid(True)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "Forecast2026_pH.png",
    dpi=300
)

plt.close()

# ==================================================
# BOD
# ==================================================

plt.figure(figsize=(10,5))

plt.plot(
    months,
    monthly["Pred_BOD"],
    marker="o",
    linewidth=2
)

plt.title("2026 Forecast - Average BOD")
plt.xlabel("Month")
plt.ylabel("BOD (mg/L)")
plt.grid(True)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "Forecast2026_BOD.png",
    dpi=300
)

plt.close()

# ==================================================
# WQI
# ==================================================

plt.figure(figsize=(10,5))

plt.plot(
    months,
    monthly["Predicted_WQI"],
    marker="o",
    linewidth=3
)

plt.title("2026 Forecast - Average Water Quality Index")
plt.xlabel("Month")
plt.ylabel("WQI")
plt.grid(True)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "Forecast2026_WQI.png",
    dpi=300
)

plt.close()

print("\nSaved Successfully")
print(OUTPUT_FOLDER)