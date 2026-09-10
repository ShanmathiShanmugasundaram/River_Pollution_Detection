import pandas as pd
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    data_folder = PROJECT_DIR / "Processed_Data"


    do = pd.read_csv(data_folder / "Master_DO.csv")
    ph = pd.read_csv(data_folder / "Master_PH.csv")
    bod = pd.read_csv(data_folder / "Master_BOD.csv")


    keys = [
        "Year",
        "Month_No",
        "Month",
        "Round",
        "State",
        "Station Code",
        "Station Name"
    ]


    print("DO Records :", len(do))
    print("PH Records :", len(ph))
    print("BOD Records :", len(bod))


    merged = do.merge(
        ph,
        on=keys,
        how="inner"
    )


    merged = merged.merge(
        bod,
        on=keys,
        how="inner"
    )


    print("\nFinal Dataset")
    print(merged.shape)

    print("\nColumns")
    print(merged.columns)


    print("\nMissing Values")
    print(merged.isnull().sum())


    output = data_folder / "Final_Water_Quality_Dataset.csv"

    merged.to_csv(output, index=False)


    print("\nSaved Successfully")
    print(output)



if __name__ == "__main__":
    main()