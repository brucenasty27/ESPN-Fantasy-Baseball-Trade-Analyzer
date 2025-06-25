import os
import pandas as pd

from scrapers.scrape_fangraphs_hitters import fetch_fangraphs_hitters
from scrapers.scrape_fangraphs_pitchers import fetch_fangraphs_pitchers

DATA_DIR = "data"
OUTPUT_CSV = os.path.join(DATA_DIR, "dynasty_rankings_cleaned.csv")

def compute_dynasty_value(row):
    # Compute dynasty value differently for pitchers and hitters based on stats
    
    position = str(row.get("position", "")).upper()
    pitcher_positions = {"SP", "RP", "P"}

    if position in pitcher_positions:
        # Pitcher dynasty value
        w = row.get("W", 0)
        sv = row.get("SV", 0)
        k = row.get("K", 0)
        era = row.get("ERA", 4.0)
        whip = row.get("WHIP", 1.3)
        ip = row.get("IP", 0)

        era_score = max(0, 4.0 - era) * 20.0
        whip_score = max(0, 1.3 - whip) * 30.0

        value = (
            w * 5.0 +
            sv * 5.0 +
            k * 1.0 +
            era_score +
            whip_score +
            ip * 0.5
        )
    else:
        # Hitter dynasty value
        hr = row.get("HR", 0)
        r = row.get("R", 0)
        rbi = row.get("RBI", 0)
        sb = row.get("SB", 0)
        avg = row.get("AVG", 0)
        bb = row.get("BB", 0)

        value = (
            hr * 4.0 +
            r * 1.0 +
            rbi * 1.0 +
            sb * 2.0 +
            avg * 50.0 +  # scale batting average
            bb * 1.0
        )
    return round(value, 2)

def update_rankings():
    print("Fetching hitters data from FanGraphs...")
    hitters_df = fetch_fangraphs_hitters()
    print(f"Fetched {len(hitters_df)} hitters")

    print("Fetching pitchers data from FanGraphs...")
    pitchers_df = fetch_fangraphs_pitchers()
    print(f"Fetched {len(pitchers_df)} pitchers")

    # Combine hitters and pitchers data
    df = pd.concat([hitters_df, pitchers_df], ignore_index=True)

    # Normalize columns for expected stats, fill missing with zeros
    stat_columns = ["HR", "R", "RBI", "SB", "AVG", "BB", "W", "SV", "K", "ERA", "WHIP", "IP"]
    for col in stat_columns:
        if col not in df.columns:
            df[col] = 0

    # Ensure position column exists
    if "position" not in df.columns:
        df["position"] = ""

    # Calculate dynasty value
    df["dynasty_value"] = df.apply(compute_dynasty_value, axis=1)

    # Create rankings based on dynasty_value (descending)
    df = df.sort_values("dynasty_value", ascending=False).reset_index(drop=True)
    df["overall_rank"] = df.index + 1

    # Position rank within each position group
    df["pos_rank"] = df.groupby("position")["dynasty_value"] \
                      .rank(method="first", ascending=False).astype(int)

    # Normalize player names to lowercase stripped for consistency
    df["name"] = df["name"].astype(str).str.strip().str.lower()
    df["position"] = df["position"].astype(str).str.upper()

    # Save to CSV
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Updated dynasty rankings saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    update_rankings()
