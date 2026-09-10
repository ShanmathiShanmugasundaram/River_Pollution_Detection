import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    input_file = (
        PROJECT_DIR /
        "Processed_Data" /
        "Final_Water_Quality_Dataset.csv"
    )


    output_file = (
        PROJECT_DIR /
        "Processed_Data" /
        "Clean_Water_Quality_Dataset.csv"
    )


    df = pd.read_csv(input_file)


    print("Before Cleaning")
    print(df.dtypes)


    # Convert numerical columns

    df["DO"] = pd.to_numeric(
        df["DO"],
        errors="coerce"
    )


    df["BOD"] = pd.to_numeric(
        df["BOD"],
        errors="coerce"
    )


    df["pH"] = pd.to_numeric(
        df["pH"],
        errors="coerce"
    )


    # Remove invalid rows

    df = df.dropna(
        subset=["DO","BOD","pH"]
    )


    # Sort chronologically

    df = df.sort_values(
        [
            "Station Code",
            "Year",
            "Month_No",
            "Round"
        ]
    )


    print("\nAfter Cleaning")

    print(df.dtypes)


    print("\nShape")

    print(df.shape)


    df.to_csv(
        output_file,
        index=False
    )


    print("\nSaved:")
    print(output_file)



if __name__ == "__main__":
    main()