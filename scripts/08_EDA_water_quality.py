import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    file = PROJECT_DIR / "Processed_Data" / "Final_Water_Quality_Dataset.csv"

    df = pd.read_csv(file)


    print("\n==============================")
    print("DATASET INFORMATION")
    print("==============================")

    print(df.info())


    print("\nDataset Shape")
    print(df.shape)


    print("\nColumns")
    print(df.columns)


    print("\nFirst Records")
    print(df.head())


    print("\n==============================")
    print("YEAR DISTRIBUTION")
    print("==============================")

    print(df.groupby("Year").size())


    print("\n==============================")
    print("STATE DISTRIBUTION")
    print("==============================")

    print(df.groupby("State")["Station Code"].nunique())


    print("\n==============================")
    print("PARAMETER STATISTICS")
    print("==============================")

    print(df[["DO","pH","BOD"]].describe())


    print("\n==============================")
    print("MISSING VALUES")
    print("==============================")

    print(df.isnull().sum())


    print("\n==============================")
    print("STATION HISTORY")
    print("==============================")

    station_count = (
        df.groupby("Station Code")
        ["Year"]
        .nunique()
    )

    print(station_count.describe())


if __name__ == "__main__":
    main()