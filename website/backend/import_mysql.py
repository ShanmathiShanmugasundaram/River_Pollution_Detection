"""Load the existing processed CSV exports into the MySQL schema.

This importer does not call the forecasting model or alter any model artefact.
"""
import os
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Processed_Data"

for env_candidate in (WEBSITE_DIR / ".env", BACKEND_DIR / ".env", ROOT / ".env"):
    if env_candidate.exists():
        load_dotenv(env_candidate)
load_dotenv()

connection = pymysql.connect(
    host=os.environ["MYSQL_HOST"], port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"],
    database=os.getenv("MYSQL_DATABASE", "ganga_water_quality"), autocommit=False,
)

def insert_rows(cursor, table, columns, rows):
    placeholders = ",".join(["%s"] * len(columns))
    names = ",".join(columns)
    cursor.executemany(f"INSERT IGNORE INTO {table} ({names}) VALUES ({placeholders})", rows)

forecast = pd.read_csv(DATA / "Forecast_2026_WQI.csv")
hotspots = pd.read_csv(DATA / "Hotspot_Analysis_2026.csv")
biological = pd.read_csv(DATA / "Seasonal_WQI_Saprobic_Validation.csv")
historical = pd.read_csv(DATA / "Final_Water_Quality_Dataset.csv")

with connection.cursor() as cursor:
    stations = pd.concat([
        forecast[["Station Code", "Station Name", "State"]],
        historical[["Station Code", "Station Name", "State"]],
    ]).drop_duplicates(subset=["Station Code"])
    insert_rows(cursor, "stations", ["station_code", "station_name", "state"], stations.astype(str).to_records(index=False).tolist())
    historical_columns = ["Station Code", "Station Name", "State", "Year", "Month_No", "Round", "DO", "pH", "BOD"]
    historical_names = ["station_code", "station_name", "state", "observation_year", "observation_month_no", "round_no", "do_value", "ph_value", "bod_value"]
    insert_rows(cursor, "historical_water_quality", historical_names, historical[historical_columns].to_records(index=False).tolist())
    insert_rows(cursor, "forecast_2026", ["station_code", "forecast_year", "forecast_month_no", "forecast_month", "forecast_round", "pred_do", "pred_ph", "pred_bod"], forecast[["Station Code", "Forecast_Year", "Forecast_Month_No", "Forecast_Month", "Forecast_Round", "Pred_DO", "Pred_pH", "Pred_BOD"]].to_records(index=False).tolist())
    insert_rows(cursor, "wqi_predictions", ["station_code", "forecast_month_no", "pred_wqi", "predicted_class"], forecast[["Station Code", "Forecast_Month_No", "Pred_WQI", "Predicted_Class"]].to_records(index=False).tolist())
    hotspot_columns = ["Station Code", "Forecast_Months", "Mean_WQI", "Min_WQI", "Mean_DO", "Min_DO", "Mean_pH", "Min_pH", "Max_pH", "Mean_BOD", "Max_BOD", "BOD_Exceed_Months", "DO_Violation_Months", "pH_Violation_Months", "Any_CPCB_Violation_Months", "BOD_Exceed_Percent", "DO_Violation_Percent", "pH_Violation_Percent", "CPCB_Violation_Percent", "Hotspot_Level"]
    hotspot_names = ["station_code", "forecast_months", "mean_wqi", "min_wqi", "mean_do", "min_do", "mean_ph", "min_ph", "max_ph", "mean_bod", "max_bod", "bod_exceed_months", "do_violation_months", "ph_violation_months", "any_cpcb_violation_months", "bod_exceed_percent", "do_violation_percent", "ph_violation_percent", "cpcb_violation_percent", "hotspot_level"]
    insert_rows(cursor, "hotspot_analysis", hotspot_names, hotspots[hotspot_columns].to_records(index=False).tolist())
    bio_columns = ["Location", "State", "Year", "Season", "Saprobic_Score", "Biological_Quality", "Station_Code"]
    bio = biological.reindex(columns=bio_columns)
    insert_rows(cursor, "saprobic_assessment", ["location", "state", "year", "season", "saprobic_score", "biological_quality", "station_code"], bio.to_records(index=False).tolist())
connection.commit()
connection.close()
print("Imported processed forecast, WQI, hotspot, and biological data into MySQL.")
