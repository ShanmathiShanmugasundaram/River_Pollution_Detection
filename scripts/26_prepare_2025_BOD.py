import pandas as pd
import re
from pathlib import Path


# =====================================================
# Helper Functions
# =====================================================

import pandas as pd
import re
from pathlib import Path


# =====================================================
# Helper Functions
# =====================================================

def get_year(sheet_name):

    match = re.search(r"20\d{2}", sheet_name)

    if match:
        return int(match.group())

    return None


def get_state(sheet_name):

    sheet_name = sheet_name.upper()

    if sheet_name.startswith("UK"):
        return "Uttarakhand"

    elif sheet_name.startswith("UP"):
        return "Uttar Pradesh"

    elif sheet_name.startswith("BH"):
        return "Bihar"

    elif sheet_name.startswith("JH"):
        return "Jharkhand"

    elif sheet_name.startswith("WB"):
        return "West Bengal"

    else:
        return "Unknown"


# =====================================================
# Convert One Sheet
# =====================================================

def convert_sheet(file_path, sheet_name):

    year = get_year(sheet_name)
    state = get_state(sheet_name)

    print(f"Processing Sheet : {sheet_name}")

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=None
    )

    # Data starts from row 4
    df = df.iloc[3:].copy()

    df.columns = range(df.shape[1])

    # Remove empty stations
    df = df[df[0].notna()]


    month_map = {
        1:"January",
        2:"February",
        3:"March",
        4:"April",
        5:"May",
        6:"June",
        7:"July",
        8:"August",
        9:"September",
        10:"October",
        11:"November",
        12:"December"
    }


    month_columns = {
        1:[3,4],
        2:[5,6],
        3:[7,8],
        4:[9,10],
        5:[11,12],
        6:[13,14],
        7:[15,16],
        8:[17,18],
        9:[19,20],
        10:[21,22],
        11:[23,24],
        12:[25,26]
    }


    records=[]


    for _,row in df.iterrows():

        station_code = row[0]
        station_name = row[2]


        for month,cols in month_columns.items():

            for round_no,col in enumerate(cols,start=1):

                value = row[col]


                # Empty value
                if pd.isna(value):
                    continue


                value = str(value).strip()


                # Skip "-"
                if value == "-":
                    continue


                # Remove BDL notation
                value = value.replace("(BDL)", "")
                value = value.replace("(BDL )", "")
                value = value.replace("BDL", "")


                # Convert <1 to 1
                value = value.replace("<", "")


                try:
                    value = float(value)

                except:
                    continue


                records.append({

                    "Year":year,
                    "Month_No":month,
                    "Month":month_map[month],
                    "Round":round_no,
                    "State":state,
                    "Station Code":station_code,
                    "Station Name":station_name,
                    "BOD":value

                })


    return pd.DataFrame(records)
# =====================================================

def process_workbook(file_path):

    print("\n========================================")
    print("Workbook :", file_path.name)
    print("========================================")

    excel = pd.ExcelFile(file_path)

    all_data = []

    for sheet in excel.sheet_names:

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

    file = bod_folder / "Ganga-MWQM Stations_data_Jan-Dec 2025 - BOD.xlsx"

    master_df = process_workbook(file)
    print("\n===================================")
    print("MASTER DATASET CREATED")
    print("===================================")

    print("Total Records :", len(master_df))
    print("Total Stations :", master_df["Station Code"].nunique())
    print("Years :", sorted(master_df["Year"].unique()))
    print("States :", master_df["State"].unique())

    # Save CSV
    output_folder = PROJECT_DIR / "Processed_Data"
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / "BOD_2025.csv"

    master_df.to_csv(output_file, index=False)

    print("\nSaved Successfully")
    print(output_file)
    print("================================")


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    main()

