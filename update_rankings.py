import csv
from rankings import (
    fetch_razzball_hitters,
    fetch_razzball_pitchers,
    fetch_fantasypros_hitters,
    fetch_fantasypros_pitchers,
    fetch_hashtagbaseball,
    combine_rankings,
)

def write_csv(rankings, filename='dynasty_rankings.csv'):
    """
    Write the combined rankings dictionary to a CSV file.
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'overall_rank', 'pos_rank', 'position']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for player in rankings.values():
            writer.writerow(player)

def update_rankings():
    print("🔄 Fetching rankings from all sources...")
    dfs = [
        fetch_razzball_hitters(),
        fetch_razzball_pitchers(),
        fetch_fantasypros_hitters(),
        fetch_fantasypros_pitchers(),
        fetch_hashtagbaseball(),
    ]

    print("📊 Combining rankings...")
    combined = combine_rankings(dfs)

    print("💾 Saving to dynasty_rankings.csv...")
    write_csv(combined)
    print("✅ Rankings updated successfully!")

if __name__ == "__main__":
    update_rankings()
