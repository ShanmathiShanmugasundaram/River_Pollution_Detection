import pandas as pd

# Input
input_file = r"Processed_Data\Saprobic_Score.csv"

# Output
output_file = r"Processed_Data\Saprobic_Score_Classified.csv"

# Read dataset
df = pd.read_csv(input_file)

# Classify Saprobic Score
def classify(score):

    if score == 0:
        return "Unknown"

    elif score >= 7.0:
        return "Very Good"

    elif score >= 5.0:
        return "Good"

    elif score >= 3.0:
        return "Moderate"

    elif score > 1.0:
        return "Poor"

    elif score == 1.0:
        return "Severe"

    else:
        return "Unknown"


df["Biological_Quality"] = df["Saprobic_Score"].apply(classify)

# Save
df.to_csv(output_file, index=False)

print("\nCLASSIFICATION COMPLETED")

print("\nClass distribution:")
print(df["Biological_Quality"].value_counts())

print("\nSample:")
print(df.head(15).to_string(index=False))

print("\nSaved to:")
print(output_file)