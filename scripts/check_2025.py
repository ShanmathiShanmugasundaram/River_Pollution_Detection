import pandas as pd

df = pd.read_csv("Processed_Data/Final_Water_Quality_Dataset.csv")

print(df[df["Year"]==2025].head())

print(df[df["Year"]==2025].shape)

print(df[df["Year"]==2025]["Year"].unique())