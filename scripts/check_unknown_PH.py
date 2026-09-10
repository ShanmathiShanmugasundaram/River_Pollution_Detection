import pandas as pd


df = pd.read_csv(
    "Processed_Data/Master_PH.csv"
)


unknown = df[df["State"]=="Unknown"]


print("Total Unknown:")
print(len(unknown))


print("\nStation List:")
print(
    unknown[["Station Code","Station Name"]]
    .drop_duplicates()
    .to_string(index=False)
)
