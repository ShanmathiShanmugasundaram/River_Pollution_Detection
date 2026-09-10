import numpy as np
from pathlib import Path

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score


# ============================================
# Paths
# ============================================

PROJECT_DIR = Path(__file__).parent.parent

DATA_FOLDER = PROJECT_DIR / "Processed_Data"


# ============================================
# Load Results
# ============================================

prediction = np.load(
    DATA_FOLDER / "prediction_2025.npy"
)

actual = np.load(
    DATA_FOLDER / "actual_2025.npy"
)


print("="*50)
print("2025 MODEL EVALUATION")
print("="*50)


print("Actual :", actual.shape)
print("Prediction :", prediction.shape)



# ============================================
# Metrics
# ============================================

names = [
    "DO",
    "pH",
    "BOD"
]


for i,name in enumerate(names):

    mae = mean_absolute_error(
        actual[:,i],
        prediction[:,i]
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual[:,i],
            prediction[:,i]
        )
    )

    r2 = r2_score(
        actual[:,i],
        prediction[:,i]
    )


    print("\n")
    print(name)

    print("MAE  :", round(mae,4))
    print("RMSE :", round(rmse,4))
    print("R²   :", round(r2,4))



print("\nEvaluation Completed")