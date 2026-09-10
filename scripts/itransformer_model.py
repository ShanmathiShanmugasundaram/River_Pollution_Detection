import numpy as np
import torch
import torch.nn as nn
from pathlib import Path

# ============================================
# Load Training Data
# ============================================

PROJECT_DIR = Path(__file__).parent.parent
DATA_FOLDER = PROJECT_DIR / "Processed_Data"

X_train = np.load(DATA_FOLDER / "X_train_scaled.npy")
y_train = np.load(DATA_FOLDER / "y_train_scaled.npy")

print("=" * 50)
print("TRAIN DATA")
print("=" * 50)
print("X_train :", X_train.shape)
print("y_train :", y_train.shape)


# ============================================
# iTransformer Model
# ============================================

class iTransformer(nn.Module):

    def __init__(
        self,
        input_features=3,
        sequence_length=12,
        d_model=64,
        nhead=4,
        num_layers=2,
        output_features=3
    ):

        super().__init__()

        # Input Embedding
        self.embedding = nn.Linear(input_features, d_model)

        # Transformer Encoder Layer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            batch_first=True
        )

        # Transformer Encoder
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # Output Layer
        self.fc = nn.Linear(d_model, output_features)

    def forward(self, x):

        # Input:
        # (batch_size, 12, 3)

        x = self.embedding(x)

        # (batch_size, 12, 64)

        x = self.transformer(x)

        # Take the last time step
        x = x[:, -1, :]

        # (batch_size, 64)

        x = self.fc(x)

        # (batch_size, 3)

        return x


# ============================================
# Test Model
# ============================================

if __name__ == "__main__":

    model = iTransformer()

    print("\n")
    print("=" * 50)
    print("MODEL")
    print("=" * 50)
    print(model)

    sample = torch.tensor(
        X_train[:8],
        dtype=torch.float32
    )

    output = model(sample)

    print("\n")
    print("=" * 50)
    print("SHAPES")
    print("=" * 50)

    print("Input :", sample.shape)
    print("Output:", output.shape)