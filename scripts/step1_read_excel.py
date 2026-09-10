import pandas as pd

# Excel file path
file_path = r"Ganga_Dataset/DO/Uttarakhand_DO_2024_2014.xlsx"

# Read the 2024 sheet with two header rows
df = pd.read_excel(
    file_path,
    sheet_name="UK_DO_2024",
    header=[2, 3]
)

# Rename the first three columns
df.columns = [
    ("Info", "Sr.No"),
    ("Info", "STN Code"),
    ("Info", "Station Name")
] + list(df.columns[3:])

# Remove rows where Station Code is empty
df = df[df[("Info", "STN Code")].notna()]

# Convert Wide → Long
records = []

for _, row in df.iterrows():

    station_code = row[("Info", "STN Code")]
    station_name = row[("Info", "Station Name")]

    for month in [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]:

        for round_name in ["First round", "Second round"]:

            value = row[(month, round_name)]

            # Ignore empty cells and '-'
            if pd.isna(value) or value == "-":
                continue

            records.append({
                "Year": 2024,
                "Station Code": station_code,
                "Station Name": station_name,
                "Month": month,
                "Round": 1 if round_name == "First round" else 2,
                "DO": value
            })

long_df = pd.DataFrame(records)

print(long_df.head(20))