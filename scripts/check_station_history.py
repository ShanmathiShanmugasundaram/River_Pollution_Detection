import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    file = PROJECT_DIR / "Processed_Data" / "Clean_Water_Quality_Dataset.csv"

    df = pd.read_csv(file)


    print("==============================")
    print("STATION HISTORY CHECK")
    print("==============================")


    history = (
        df.groupby("Station Code")["Year"]
        .nunique()
        .sort_values()
    )


    print("\nNumber of years per station:")
    print(history)


    print("\nStatistics:")
    print(history.describe())


    print("\nStations with less than 5 years:")
    print(history[history < 5])


    print("\nTotal Stations:")
    print(df["Station Code"].nunique())


if __name__ == "__main__":
    main()