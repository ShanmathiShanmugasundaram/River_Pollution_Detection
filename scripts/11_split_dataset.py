import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    input_file = (
        PROJECT_DIR /
        "Processed_Data" /
        "Clean_Water_Quality_Dataset.csv"
    )


    output_folder = (
        PROJECT_DIR /
        "Processed_Data"
    )


    df = pd.read_csv(input_file)


    # Training data
    train_df = df[
        df["Year"] <= 2022
    ]


    # Validation data
    val_df = df[
        (df["Year"] >= 2023) &
        (df["Year"] <= 2024)
    ]


    print("==============================")
    print("TRAIN DATA")
    print("==============================")

    print(train_df.shape)
    print(train_df["Year"].unique())


    print("\n==============================")
    print("VALIDATION DATA")
    print("==============================")

    print(val_df.shape)
    print(val_df["Year"].unique())


    train_df.to_csv(
        output_folder / "train.csv",
        index=False
    )


    val_df.to_csv(
        output_folder / "validation.csv",
        index=False
    )


    print("\nSaved Successfully")


if __name__ == "__main__":
    main()