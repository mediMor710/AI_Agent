import json
import os
import logging
import pandas as pd
from config import CSV_PATH

logger = logging.getLogger(__name__)

def load() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"Sales_Data.csv not found at: {CSV_PATH}\n"
        )
    
    frame = pd.read_csv(CSV_PATH)
    frame.columns = (
        frame.columns.str.strip()
                     .str.lower()
                     # Convert any special character with '_'
                     .str.replace(r"[^a-z0-9]+",
                                   "_", regex=True)
                     .str.strip("_")
    )

    for c in frame.columns:
        if "date" in c:
            # 'coerce' fills invalid value with 'NaT'
            frame[c] = pd.to_datetime(frame[c], errors="coerce")

    return frame


df = load()
DATE_COLS = []
for c in df.columns:
    if 'date' in c:
        DATE_COLS.append(c)
NUMERIC_COLS     = df.select_dtypes(include="number").columns.tolist()
CATEGORICAL_COLS = df.select_dtypes(include="object").columns.tolist()
ALL_COLS         = list(df.columns)

# convert the first 5 rows into JSON 
# 'record' is the easier format that API could get for response
# 'iso' is the standard format of date that API accepts
SAMPLE_ROWS = json.loads(
    df.head(5).to_json(orient="records", date_format="iso")
)

# Get all the unique values for each categorical column
# These are sent to Claude so it knows exactly what values exist
CAT_VALUES = {}
for col in CATEGORICAL_COLS:
    values = (
        df[col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    values = sorted(values)
    CAT_VALUES[col] = values[:80]

def get_schema_description() -> str:

    lines = ['DataFrame columns:']
    for col in ALL_COLS:
        if col in NUMERIC_COLS:
            mn = df[col].min()
            mx = df[col].max()
            lines.append(f' {col} [numeric] - min={mn:,.2f}, max={mx:,.2f}')
        elif col in DATE_COLS:
            mn = df[col].min()
            mx = df[col].max()
            lines.append(f' {col} [date] - from {mn} to {mx}')
        else:
            # Gets the number of unique values
            n_unique = df[col].nunique()
            # Gets the first 6 values
            sample = CAT_VALUES.get(col, [])[:6]
            lines.append(f' {col} [text, {n_unique} unique] -e.g. {sample}')
    lines.append(f'\nTotal rows: {len(df):,}')

    return '\n'.join(lines)

logger.info(f'Loaded {len(df):,} rows | {len(ALL_COLS)} columns')


print(f"[data_loader] Loaded {len(df):,} rows | columns: {ALL_COLS}")