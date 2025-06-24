import pandas as pd
import os
import glob

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "dynasty_rankings_cleaned.csv")

def load_csv_files():
    # Load all CSV files in DATA_DIR matching *_rankings.csv or razzball_stats.csv
    pattern_rankings = os.path.join(DATA_DIR, "*_rankings.csv")
    pattern_razzball = os.path.join(DATA_DIR, "razzball_stats.csv")
    csv_files = glob.glob(pattern_rankings)
    if os.path.exists(pattern_razzball):
        csv_files.append(pattern_razzball)

    if not csv_files:
        print("⚠️ No ranking CSV files found in data directory!")
        return []

    dataframes = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            df["source"] = os.path.basename(f).replace("_rankings.csv", "").replace(".csv", "")
            # Standardize player names for merging
            if "name" in df.columns:
                df["name"] = df["name"].astype(str).str.strip().str.lower()
            else:
                print(f"⚠️ 'name' column missing in {f}, skipping this file")
                continue
            dataframes.append(df)
            print(f"✅ Loaded {f} with {len(df)} rows")
        except Exception as e:
            print(f"Error loading {f}: {e}")

    return dataframes

def combine_and_aggregate(dataframes):
    if not dataframes:
        print("No dataframes to combine, exiting.")
        return None

    combined = pd.concat(dataframes, ignore_index=True)
    print(f"Combined dataframe shape: {combined.shape}")

    # Aggregate overall_rank by average if available
    if "overall_rank" in combined.columns:
        agg = combined.groupby("name").agg(
            overall_rank=("overall_rank", "mean"),
            sources=("source", "nunique")
        ).reset_index()
    else:
        print("⚠️ 'overall_rank' column missing in combined data, cannot aggregate ranks.")
        agg = combined[["name"]].drop_duplicates()

    # Try to merge Razzball stats if present
    razzball_path = os.path.join(DATA_DIR, "razzball_stats.csv")
    if os.path.exists(razzball_path):
        razz_df = pd.read_csv(razzball_path)
        if "name" in razz_df.columns:
            razz_df["name"] = razz_df["name"].astype(str).str.strip().str.lower()
            agg = agg.merge(razz_df, on="name", how="left")
            print("✅ Merged Razzball stats into combined rankings")
        else:
            print("⚠️ Razzball stats missing 'name' column, skipping merge")

    # Create dynasty_value based on rank
    if "overall_rank" in agg.columns:
        agg = agg.sort_values("overall_rank").reset_index(drop=True)
        agg["dynasty_value"] = agg.index.map(lambda x: round(1000 / (x + 5), 2))
    else:
        agg["dynasty_value"] = 0

    return agg

def main():
    dfs = load_csv_files()
    combined_df = combine_and_aggregate(dfs)
    if combined_df is not None:
        combined_df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Saved combined dynasty rankings to {OUTPUT_FILE}")
    else:
        print("❌ Failed to generate combined rankings")

if __name__ == "__main__":
    main()
