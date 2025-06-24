import os
import pandas as pd
from rankings import (
    fetch_razzball_hitters,
    fetch_razzball_pitchers,
    fetch_fantasypros_hitters,
    fetch_fantasypros_pitchers,
    fetch_hashtagbaseball,
    fetch_statcast_advanced,
    combine_rankings,
)

OUTPUT_FILE = "data/dynasty_rankings_cleaned.csv"

def ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")

def main():
    print("🔄 Starting dynasty rankings update...")

    print("Fetching Razzball hitters...")
    rb_hitters = fetch_razzball_hitters()

    print("Fetching Razzball pitchers...")
    rb_pitchers = fetch_razzball_pitchers()

    print("Fetching FantasyPros hitters...")
    fp_hitters = fetch_fantasypros_hitters()

    print("Fetching FantasyPros pitchers...")
    fp_pitchers = fetch_fantasypros_pitchers()

    print("Fetching Hashtag Baseball rankings...")
    hashtag_df = fetch_hashtagbaseball()

    print("Combining rankings...")
    combined_raw = combine_rankings([
        rb_hitters, rb_pitchers,
        fp_hitters, fp_pitchers,
        hashtag_df
    ])

    print("Fetching advanced stats (WAR, OPS, SLG, OPS+)...")
    statcast_data = fetch_statcast_advanced()

    print("Merging advanced stats into combined rankings...")
    final_records = []
    for name, data in combined_raw.items():
        stats = statcast_data.get(name, {
            "WAR": 0, "OPS": 0, "SLG": 0, "OPS+": 0, "dynasty_value": 0
        })
        dynasty_value = round((1000 / (1 + data["overall_rank"])) + stats.get("WAR", 0), 2)
        final_records.append({
            "name": name,
            "overall_rank": round(data["overall_rank"], 2),
            "pos_rank": round(data["pos_rank"], 2),
            "position": data.get("position", ""),
            "WAR": stats.get("WAR", 0),
            "OPS": stats.get("OPS", 0),
            "SLG": stats.get("SLG", 0),
            "OPS+": stats.get("OPS+", 0),
            "dynasty_value": dynasty_value
        })

    df_final = pd.DataFrame(final_records)
    df_final.sort_values("dynasty_value", ascending=False, inplace=True)

    ensure_data_dir()

    print(f"Exporting combined rankings to {OUTPUT_FILE}...")
    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved combined rankings to {OUTPUT_FILE}")
    print("✅ Dynasty rankings update completed successfully!")

if __name__ == "__main__":
    main()
