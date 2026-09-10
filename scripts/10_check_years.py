import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    file = (
        PROJECT_DIR /
        "Processed_Data" /
        "Clean_Water_Quality_Dataset.csv"
    )

    df = pd.read_csv(file)


    print(df.groupby("Year").size())


    print("\nMinimum Year:")
    print(df["Year"].min())


    print("\nMaximum Year:")
    print(df["Year"].max())


if __name__ == "__main__":
    main()