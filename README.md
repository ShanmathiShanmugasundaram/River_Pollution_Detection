# 🌊 Ganga River Water Quality Forecasting using iTransformer

## Project Overview

This project proposes an **iTransformer-based deep learning framework** for forecasting the water quality of the **River Ganga** using historical monitoring data.

The model predicts three important water quality parameters:

- Dissolved Oxygen (DO)
- pH
- Biological Oxygen Demand (BOD)

The predicted values are further used to calculate the **Water Quality Index (WQI)** and classify river water quality into different categories.

Unlike traditional machine learning approaches, the proposed model learns long-term temporal dependencies using the **iTransformer architecture**, making it suitable for multivariate time-series forecasting.

---

# Objectives

- Develop a deep learning model for river water quality forecasting.
- Predict DO, pH, and BOD simultaneously.
- Calculate Water Quality Index (WQI).
- Forecast future river water quality (2026).
- Assist environmental agencies in proactive water quality monitoring.

---

# Dataset

### Source

Manual Water Quality Monitoring (MWQM) Stations

River Ganga Monitoring Data

Years:
- 2014 – 2025

States Covered

- Uttarakhand
- Uttar Pradesh
- Bihar
- Jharkhand
- West Bengal

---

# Features Used

| Feature | Description |
|----------|-------------|
| DO | Dissolved Oxygen |
| pH | Acidity/Alkalinity |
| BOD | Biological Oxygen Demand |

---

# Project Workflow

```
Raw Excel Dataset
        │
        ▼
Data Cleaning
        │
        ▼
Feature Extraction
(DO, pH, BOD)
        │
        ▼
Sequence Generation
(12 Time Steps)
        │
        ▼
Data Scaling
(StandardScaler)
        │
        ▼
iTransformer Training
        │
        ▼
Prediction
        │
        ▼
Model Evaluation
        │
        ▼
Water Quality Index (WQI)
        │
        ▼
2026 Water Quality Forecast
```

---

# Folder Structure

```
River_Water_Quality_Project/

│
├── Ganga_Dataset/
│     ├── DO/
│     ├── PH/
│     └── BOD/
│
├── Processed_Data/
│     ├── train.csv
│     ├── validation.csv
│     ├── X_train.npy
│     ├── y_train.npy
│     ├── X_val.npy
│     ├── y_val.npy
│     ├── Test_2025_Dataset.csv
│     ├── Forecast_2026.csv
│     ├── Forecast_2026_WQI.csv
│     └── scaler files
│
├── models/
│     └── best_itransformer.pth
│
├── output/
│     ├── WQI plots
│     ├── Forecast plots
│     └── Evaluation graphs
│
├── scripts/
│     ├── Data preprocessing
│     ├── Sequence generation
│     ├── Model training
│     ├── Model testing
│     ├── WQI calculation
│     └── Forecast generation
│
└── README.md
```

---

# Model Architecture

Model Used:

**iTransformer**

Input

```
12 Months
↓

DO
pH
BOD
```

Output

```
Next Month

↓

Predicted DO
Predicted pH
Predicted BOD
```

---

# Data Preprocessing

The preprocessing pipeline includes:

- Missing value removal
- Invalid symbol handling
- BDL value conversion
- Monthly sequence generation
- Station-wise sorting
- StandardScaler normalization

---

# Model Training

Training Data

```
2014–2024
```

Testing Data

```
2025
```

Forecast

```
2026
```

Sequence Length

```
12 Months
```

Loss Function

```
Mean Squared Error (MSE)
```
---

# Evaluation Metrics

The model was evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- Coefficient of Determination (R²)

### 2025 Test Results

| Parameter | MAE | RMSE | R² |
|------------|------|------|------|
| DO | 0.431 | 0.585 | 0.740 |
| pH | 0.175 | 0.234 | 0.674 |
| BOD | 0.289 | 0.377 | 0.820 |

---

# Water Quality Index (WQI)

The predicted parameters are converted into Water Quality Index values.

Water quality categories:

| WQI | Category |
|------|----------|
| 90–100 | Excellent |
| 70–90 | Good |
| 50–70 | Medium |
| 25–50 | Poor |
| 0–25 | Very Poor |

---

# 2026 Forecast

The trained model recursively forecasts:

- January 2026
- February 2026
- ...
- December 2026

Monthly predictions include:

- DO
- pH
- BOD
- Water Quality Index

---

# Technologies Used

- Python
- NumPy
- Pandas
- PyTorch
- Scikit-learn
- Matplotlib

---

# Project Highlights

✔ End-to-End Deep Learning Pipeline

✔ Multivariate Time-Series Forecasting

✔ iTransformer-based Prediction

✔ Water Quality Index Calculation

✔ 2026 Future Forecast Generation

✔ Evaluation on Unseen 2025 Data

---
License

This project is intended for academic and research purposes.
