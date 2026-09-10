import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    input_file = PROJECT_DIR / "Processed_Data" / "Clean_Water_Quality_Dataset.csv"

    output_file = PROJECT_DIR / "Processed_Data" / "Filtered_Water_Quality_Dataset.csv"


    df = pd.read_csv(input_file)


    print("==============================")
    print("BEFORE FILTERING")
    print("==============================")

    print("Records :", len(df))
    print("Stations :", df["Station Code"].nunique())


    # Count years available for each station
    station_years = (
        df.groupby("Station Code")["Year"]
        .nunique()
    )


    print("\nStation History:")
    print(station_years.describe())


    # Keep stations having minimum 5 years data
    valid_stations = station_years[
        station_years >= 5
    ].index


    filtered_df = df[
        df["Station Code"].isin(valid_stations)
    ]


    print("\n==============================")
    print("AFTER FILTERING")
    print("==============================")


    print("Records :", len(filtered_df))
    print("Stations :", filtered_df["Station Code"].nunique())


    print("\nRemoved Stations:")
    print(
        df["Station Code"].nunique()
        -
        filtered_df["Station Code"].nunique()
    )


    filtered_df.to_csv(
        output_file,
        index=False
    )


    print("\nSaved Successfully")
    print(output_file)



if __name__ == "__main__":
    main()