import numpy as np
import pandas as pd
from pathlib import Path


# ===========================================
# Configuration
# ===========================================

SEQUENCE_LENGTH = 12


# ===========================================
# Main
# ===========================================

def main():

    PROJECT_DIR = Path(__file__).parent.parent

    input_file = (
        PROJECT_DIR /
        "Processed_Data" /
        "Filtered_Water_Quality_Dataset.csv"
    )

    df = pd.read_csv(input_file)

    print("=" * 50)
    print("CREATING TIME SERIES SEQUENCES")
    print("=" * 50)

    # ---------------------------------------
    # Sort data
    # ---------------------------------------

    df = df.sort_values(
        [
            "Station Code",
            "Year",
            "Month_No",
            "Round"
        ]
    ).reset_index(drop=True)

    X = []
    y = []

    stations_used = 0

    # ---------------------------------------
    # Create sequences station by station
    # ---------------------------------------

    for station, station_df in df.groupby("Station Code"):

        station_df = station_df.reset_index(drop=True)

        features = station_df[
            [
                "DO",
                "pH",
                "BOD"
            ]
        ].values

        if len(features) <= SEQUENCE_LENGTH:
            continue

        stations_used += 1

        for i in range(len(features) - SEQUENCE_LENGTH):

            X.append(
                features[
                    i:i + SEQUENCE_LENGTH
                ]
            )

            y.append(
                features[
                    i + SEQUENCE_LENGTH
                ]
            )

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    print("\nStations Used :", stations_used)

    print("\nInput Shape (X)")
    print(X.shape)

    print("\nTarget Shape (y)")
    print(y.shape)

    # ---------------------------------------
    # Save
    # ---------------------------------------

    output_folder = (
        PROJECT_DIR /
        "Processed_Data"
    )

    np.save(
        output_folder / "X_sequences.npy",
        X
    )

    np.save(
        output_folder / "y_targets.npy",
        y
    )

    print("\nSaved Successfully")

    print(output_folder / "X_sequences.npy")
    print(output_folder / "y_targets.npy")


if __name__ == "__main__":
    main()