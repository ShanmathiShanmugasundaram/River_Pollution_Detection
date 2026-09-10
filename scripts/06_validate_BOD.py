import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    file = PROJECT_DIR / "Processed_Data" / "Master_BOD.csv"

    df = pd.read_csv(file)


    print("\nDataset Shape")
    print(df.shape)


    print("\nColumns")
    print(df.columns)


    print("\nMissing Values")
    print(df.isnull().sum())


    print("\nFirst 5 Records")
    print(df.head())


    print("\nStation Distribution")
    print(df.groupby("State")["Station Code"].nunique())


    print("\nYear Distribution")
    print(df.groupby("Year").size())


if __name__ == "__main__":
    main()