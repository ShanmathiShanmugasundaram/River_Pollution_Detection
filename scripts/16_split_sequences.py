import numpy as np
from pathlib import Path


def main():

    PROJECT_DIR = Path(__file__).parent.parent

    X = np.load(PROJECT_DIR / "Processed_Data" / "X_sequences.npy")
    y = np.load(PROJECT_DIR / "Processed_Data" / "y_targets.npy")

    print("=" * 50)
    print("SEQUENCE SPLITTING")
    print("=" * 50)

    total = len(X)

    train_size = int(total * 0.8)

    X_train = X[:train_size]
    y_train = y[:train_size]

    X_val = X[train_size:]
    y_val = y[train_size:]

    print("\nTraining Samples :", len(X_train))
    print("Validation Samples :", len(X_val))

    print("\nX_train :", X_train.shape)
    print("y_train :", y_train.shape)

    print("\nX_val :", X_val.shape)
    print("y_val :", y_val.shape)

    output = PROJECT_DIR / "Processed_Data"

    np.save(output / "X_train.npy", X_train)
    np.save(output / "y_train.npy", y_train)

    np.save(output / "X_val.npy", X_val)
    np.save(output / "y_val.npy", y_val)

    print("\nSaved Successfully")


if __name__ == "__main__":
    main()