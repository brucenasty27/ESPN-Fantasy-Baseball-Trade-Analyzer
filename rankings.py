import pandas as pd
import numpy as np

# Define the paths to your scraper CSV files
SCRAPER_FILES = {
    "cbssports": "data/cbssports_rankings.csv",
    "espn_hitters": "data/espn_hitters.csv",
    "espn_pitchers": "data/espn_pitchers.csv",
    "fangraphs_hitters": "data/fangraphs_hitters.csv",
    "fangraphs_pitchers": "data/fangraphs_pitchers.csv",
    "fantasypros": "data/fantasypros_combined_rankings.csv",
    "fantraxhq": "data/fantraxhq_rankings.csv",
    "mlbpipeline": "data/mlbpipeline_prospects.csv",
    "pitcherlist": "data/pitcherlist_rankings.csv",
    "prospectslive": "data/prospectslive_rankings.csv",
    "rotoballer": "data/rotoballer_rankings.csv",
    "rotowire": "data/rotowire_rankings.csv",
}

# Standard column sets
HITTER_STATS = ["HR", "R", "RBI", "SB", "BB", "AVG"]
PITCHER_STATS = ["W", "SV", "K", "ERA", "WHIP"]

# ESPN-style stat weights for dynasty value calculation
STAT_WEIGHTS = {
    # Hitters
    "HR": 1.5,
    "R": 1.2,
    "RBI": 1.3,
    "SB": 2.0,
    "BB": 1.0,
    "AVG": 20.0,  # scaled because AVG is decimal <1

    # Pitchers
    "W": 5.0,
    "SV": 8.0,
    "K": 1.0,
    "ERA": -20.0,  # negative because lower ERA is better
    "WHIP": -25.0  # negative because lower WHIP is better
}

def load_and_prepare(path, expected_columns):
    """
    Load a CSV, ensure expected columns exist, normalize names.
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"Warning: File not found: {path}")
        return pd.DataFrame()

    # Lowercase and strip names for consistency
    df["name"] = df["name"].astype(str).str.lower().str.strip()

    # Ensure all expected columns exist, fill missing with 0 or ''
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0 if col not in ["name", "position"] else ""

    # Convert numeric columns to numeric types
    for col in expected_columns:
        if col not in ["name", "position"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Ensure position column exists
    if "position" not in df.columns:
        df["position"] = ""

    return df

def merge_dataframes(dfs):
    """
    Merge multiple DataFrames on player 'name' and 'position' using outer join.
    For stats columns, take the max or mean across sources.
    """
    if not dfs:
        return pd.DataFrame()

    combined = dfs[0]

    for df in dfs[1:]:
        combined = pd.merge(combined, df, on=["name", "position"], how="outer", suffixes=("", "_y"))

        # For each stat column, resolve duplicates by picking max or mean
        for col in HITTER_STATS + PITCHER_STATS + ["overall_rank", "pos_rank"]:
            col_y = f"{col}_y"
            if col in combined.columns and col_y in combined.columns:
                combined[col] = combined[[col, col_y]].max(axis=1, skipna=True)
                combined.drop(columns=[col_y], inplace=True)
            elif col_y in combined.columns:
                combined[col] = combined[col_y]
                combined.drop(columns=[col_y], inplace=True)

    return combined

def calculate_dynasty_value(df):
    """
    Calculate dynasty_value for hitters and pitchers based on stat weights.
    Negative weights apply to ERA and WHIP.
    """
    df = df.copy()

    # Separate hitters and pitchers by position codes
    pitcher_positions = {"sp", "rp", "p"}
    df["is_pitcher"] = df["position"].str.lower().isin(pitcher_positions)

    # Fill missing stats with 0
    for stat in HITTER_STATS + PITCHER_STATS:
        if stat not in df.columns:
            df[stat] = 0

    # Calculate hitters dynasty value
    def hitter_value(row):
        return sum(row[stat] * STAT_WEIGHTS.get(stat, 0) for stat in HITTER_STATS)

    # Calculate pitchers dynasty value
    def pitcher_value(row):
        # Note ERA and WHIP are negative weights, so multiply accordingly
        era_val = row.get("ERA", 0)
        whip_val = row.get("WHIP", 0)
        return (
            row.get("W", 0) * STAT_WEIGHTS["W"] +
            row.get("SV", 0) * STAT_WEIGHTS["SV"] +
            row.get("K", 0) * STAT_WEIGHTS["K"] +
            era_val * STAT_WEIGHTS["ERA"] +
            whip_val * STAT_WEIGHTS["WHIP"]
        )

    df["dynasty_value"] = 0
    df.loc[~df["is_pitcher"], "dynasty_value"] = df.loc[~df["is_pitcher"]].apply(hitter_value, axis=1)
    df.loc[df["is_pitcher"], "dynasty_value"] = df.loc[df["is_pitcher"]].apply(pitcher_value, axis=1)

    # Optional: normalize dynasty_value to 0-100 scale for easier interpretation
    min_val = df["dynasty_value"].min()
    max_val = df["dynasty_value"].max()
    if max_val > min_val:
        df["dynasty_value_norm"] = (df["dynasty_value"] - min_val) / (max_val - min_val) * 100
    else:
        df["dynasty_value_norm"] = 0

    return df

def assign_ranks(df):
    """
    Assign overall rank and positional rank based on dynasty_value.
    """
    df = df.copy()
    df = df.sort_values("dynasty_value", ascending=False).reset_index(drop=True)
    df["overall_rank"] = df.index + 1

    # Positional ranks
    df["pos_rank"] = df.groupby("position")["dynasty_value"].rank(method="min", ascending=False).astype(int)

    return df

def main():
    print("Loading and preparing data from all scrapers...")
    dfs = []

    # Load hitters data sources
    hitters_sources = [
        "cbssports",
        "espn_hitters",
        "fangraphs_hitters",
        "fantasypros",
        "fantraxhq",
        "mlbpipeline",
        "prospectslive",
        "rotoballer",
        "rotowire"
    ]

    # Load pitchers data sources
    pitchers_sources = [
        "espn_pitchers",
        "fangraphs_pitchers",
        "fantasypros",
        "fantraxhq",
        "pitcherlist",
        "prospectslive",
        "rotoballer",
        "rotowire"
    ]

    # Prepare hitters dfs
    for source in hitters_sources:
        path = SCRAPER_FILES.get(source)
        if not path:
            continue
        df = load_and_prepare(path, ["name", "overall_rank", "pos_rank", "position"] + HITTER_STATS)
        dfs.append(df)

    # Prepare pitchers dfs
    for source in pitchers_sources:
        path = SCRAPER_FILES.get(source)
        if not path:
            continue
        df = load_and_prepare(path, ["name", "overall_rank", "pos_rank", "position"] + PITCHER_STATS)
        dfs.append(df)

    print(f"Loaded {len(dfs)} dataframes, merging now...")
    combined = merge_dataframes(dfs)

    print(f"Calculating dynasty values for {len(combined)} players...")
    combined = calculate_dynasty_value(combined)

    print("Assigning ranks...")
    combined = assign_ranks(combined)

    # Save final cleaned file
    combined.to_csv("data/dynasty_rankings_cleaned.csv", index=False)
    print(f"✅ Saved cleaned dynasty rankings ({len(combined)}) to data/dynasty_rankings_cleaned.csv")

if __name__ == "__main__":
    main()
