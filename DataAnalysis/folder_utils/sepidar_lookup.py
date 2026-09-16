import datetime

import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz
from Constatns import Constants
from DataAnalysis.models import FoodItems
from user_management.utils import check_server

# -----------------------------
# Normalization
# -----------------------------
def normalize_fa(text: str) -> str:
    return (
        text.replace("ي", "ی")
            .replace("ك", "ک")
            .replace("\u200c", "")
            .strip()
    )


# Load once at import time
SERVER = check_server()

if SERVER:
    EXCEL_PATH = Path(r"/home/seketal1/Seketala_Kitchen_Flow/cache/sepidar_food_code.xlsx")  # adjust path
else:
    EXCEL_PATH = Path(r"cache\sepidar_food_code.xlsx")

_df = pd.read_excel(EXCEL_PATH, dtype=str)

_df["كد"] = _df["كد"].astype(str).str.strip()
_df["عنوان"] = _df["عنوان"].apply(normalize_fa)

# Build NAME -> CODE map
_NAME_TO_CODE = dict(zip(_df["عنوان"], _df["كد"]))
_NAMES = list(_NAME_TO_CODE.keys())

# -----------------------------
# Fuzzy lookup (≥ 90%)

# -----------------------------


CODE_BY_DATE={
    2100018:1100085,
    2100001:1100086,
    2500013:1100088,
    1100066:1100087,
    1100082:1100082,
    1100082:1100082,
    1100082:1100082,
    1100082:1100082,
}


def get_code_by_name(name: str, threshold: int = 90,date=None) -> str | None:
    if not name:
        return None
    
    if Constants.OLD_GET_FOOD_DATA:

        name = normalize_fa(name)

        match = process.extractOne(
            name,
            _NAMES,
            scorer=fuzz.ratio
        )

        if match and match[1] >= threshold:
            matched_name = match[0]

            code = _NAME_TO_CODE[matched_name]
            if date:
                target_date = datetime.datetime(2026, 7, 23,0,0,0)
                if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
                    date = datetime.datetime.combine(date, datetime.time.min)


                if date>=target_date:
                    if int(code) in CODE_BY_DATE.keys():
                        code =str(CODE_BY_DATE[int(code)])
            return code


        return None

    else:
        name_obj = FoodItems.objects.filter(food_name=name)
        if not name_obj.exists() :
            print('Sepidar code not exist for name : ',name)
            # error_factors.append(f'Name Not Exist :{it.food_name} ' )  # Add invoice number to error list
            return None
        name_obj = name_obj.first()
        sepdar_code = name_obj.sepdar_code
        return sepdar_code


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":
    print(get_code_by_name("ماشروم برگر"))      # exact
    print(get_code_by_name("ماشرومبرگر"))       # missing space
    print(get_code_by_name("ماشروم برکر"))      # typo
