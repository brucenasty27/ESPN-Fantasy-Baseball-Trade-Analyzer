import pandas as pd
import re

INPUT_FILE = "dynasty_rankings.csv"
OUTPUT_FILE = "dynasty_rankings_cleaned.csv"

# Ensure player name format is consistent
def clean_player_name(name):
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

required_columns = [
    "name", "overall_rank", "pos_rank", "position",
    "dynasty_value", "WAR", "OPS", "SLG", "OPS+"
]

def validate_and_clean():
    try:
        df = pd.read_csv(INPUT_FILE)

        # Ensure required columns
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            print(f"ERROR: Missing columns in CSV: {missing}")
            return

        # Clean name column
        df["name"] = df["name"].astype(str).apply(clean_player_name)

        # Enforce numeric types (fill invalid with 0)
        for col in ["overall_rank", "pos_rank", "dynasty_value", "WAR", "OPS", "SLG", "OPS+"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Drop any rows missing required data
        df.dropna(subset=["name", "position"], inplace=True)

        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Cleaned and validated rankings saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error during validation: {e}")

if __name__ == "__main__":
    validate_and_clean()
