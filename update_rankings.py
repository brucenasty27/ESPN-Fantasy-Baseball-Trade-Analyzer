# update_rankings.py

import rankings
import sys

def main():
    print("🔄 Starting dynasty rankings update...")

    try:
        print("Fetching Razzball hitters...")
        hitters_rb = rankings.fetch_razzball_hitters()

        print("Fetching Razzball pitchers...")
        pitchers_rb = rankings.fetch_razzball_pitchers()

        print("Fetching FantasyPros hitters...")
        hitters_fp = rankings.fetch_fantasypros_hitters()

        print("Fetching FantasyPros pitchers...")
        pitchers_fp = rankings.fetch_fantasypros_pitchers()

        print("Fetching Hashtag Baseball rankings...")
        hashtag = rankings.fetch_hashtagbaseball()

        # Combine all sources
        print("Combining rankings...")
        combined = rankings.combine_rankings([hitters_rb, pitchers_rb, hitters_fp, pitchers_fp, hashtag])

        # Fetch advanced stats
        print("Fetching advanced stats (WAR, OPS, SLG, OPS+)...")
        advanced = rankings.fetch_statcast_advanced()

        # Merge advanced stats into combined rankings
        print("Merging advanced stats into combined rankings...")
        combined_with_stats = rankings.merge_advanced_stats(combined, advanced)

        # Export final combined rankings CSV
        print("Exporting combined rankings to dynasty_rankings_cleaned.csv...")
        rankings.export_combined_rankings_to_csv(combined_with_stats)

        print("✅ Dynasty rankings update completed successfully!")

    except Exception as e:
        print(f"❌ Error during rankings update: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
