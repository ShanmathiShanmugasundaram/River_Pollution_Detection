import pandas as pd
import re
from pathlib import Path


# =====================================================
# Helper Functions
# =====================================================

def get_year(sheet_name):
    match = re.search(r"\d{4}$", sheet_name)

    if match:
        return int(match.group())

    return None


def get_state(file_name):

    file_name = file_name.lower()


    if "uttarakhand" in file_name:
        return "Uttarakhand"

    elif "uttar pradesh" in file_name:
        return "Uttar Pradesh"

    elif "bihar" in file_name:
        return "Bihar"

    elif "jharkhand" in file_name:
        return "Jharkhand"

    elif "westbengal" in file_name or "west_bengal" in file_name:
        return "West Bengal"

    else:
        return "Unknown"


# =====================================================
# Convert One Sheet
# =====================================================

def convert_sheet(file_path, sheet_name):

    year = get_year(sheet_name)
    state = get_state(file_path.name)

    print(f"Processing Sheet : {sheet_name}")

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=[2, 3]
    )

    # Rename first three columns
    new_columns = [
        ("Info", "Sr.No"),
        ("Info", "Station Code"),
        ("Info", "Station Name")
    ]

    new_columns.extend(df.columns[3:])

    df.columns = pd.MultiIndex.from_tuples(new_columns)

    # Remove empty stations
    df = df[df[("Info", "Station Code")].notna()]

    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }

    records = []

    for _, row in df.iterrows():

        station_code = row[("Info", "Station Code")]
        station_name = row[("Info", "Station Name")]

        for month in month_map:

            # Find all columns for this month
            month_columns = [col for col in df.columns if col[0] == month]

            # Loop through all available rounds
            for round_no, col in enumerate(month_columns, start=1):

                value = row[col]

                # Skip empty values
                if pd.isna(value):
                    continue

                # Skip '-'
                if str(value).strip() == "-":
                    continue

                records.append({

                    "Year": year,
                    "Month_No": month_map[month],
                    "Month": month,
                    "Round": round_no,
                    "State": state,
                    "Station Code": station_code,
                    "Station Name": station_name,
                    "BOD": value

                })

    return pd.DataFrame(records)
# =====================================================
# Process One Workbook
# =====================================================

def process_workbook(file_path):

    print("\n========================================")
    print("Workbook :", file_path.name)
    print("========================================")

    excel = pd.ExcelFile(file_path)

    all_data = []

    for sheet in excel.sheet_names:

        # Skip summary sheet
        if sheet.lower() == "complete stretch":
            continue

        df = convert_sheet(file_path, sheet)

        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)

    return final_df


# =====================================================
# Main
# =====================================================

def main():

    PROJECT_DIR = Path(__file__).parent.parent

    bod_folder = PROJECT_DIR / "Ganga_Dataset" / "BOD"

    all_data = []

    excel_files = sorted(bod_folder.glob("*.xlsx"))

    print(f"\nTotal Excel Files : {len(excel_files)}\n")

    for file in excel_files:

        print("=" * 60)
        print(file.name)
        print("=" * 60)

        df = process_workbook(file)

        all_data.append(df)

    master_df = pd.concat(all_data, ignore_index=True)

    print("\n===================================")
    print("MASTER DATASET CREATED")
    print("===================================")
    master_df["Year"] = pd.to_numeric(
    master_df["Year"],
    errors="coerce"
)
    print("Total Records :", len(master_df))
    print("Total Stations :", master_df["Station Code"].nunique())
    print(
    "Years :",
    sorted(master_df["Year"].dropna().unique())
)
    print("States :", master_df["State"].unique())

    # Save CSV
    output_folder = PROJECT_DIR / "Processed_Data"
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / "Master_BOD.csv"
    master_df = master_df.dropna(subset=["Year"])
    master_df.to_csv(output_file, index=False)

    print("\nSaved Successfully")
    print(output_file)
    print("================================")


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    main()