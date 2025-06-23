import csv
from rankings import (
    fetch_razzball_hitters,
    fetch_razzball_pitchers,
    fetch_fantasypros_hitters,
    fetch_fantasypros_pitchers,
    fetch_hashtagbaseball,
    fetch_statcast_advanced,
    combine_rankings
)

def write_csv(rankings, filename='dynasty_rankings.csv'):
    """
    Write the combined rankings dictionary to a CSV file.
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'overall_rank', 'pos_rank', 'position', 'dynasty_value', 'WAR', 'OPS', 'SLG', 'OPS+']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for player_name, player_data in rankings.items():
            # Defensive fallback to ensure all fields exist
            row = {
                'name': player_name,
                'overall_rank': player_data.get('overall_rank', 9999),
                'pos_rank': player_data.get('pos_rank', 9999),
                'position': player_data.get('position', ''),
                'dynasty_value': player_data.get('dynasty_value', 0),
                'WAR': player_data.get('WAR', 0),
                'OPS': player_data.get('OPS', 0),
                'SLG': player_data.get('SLG', 0),
                'OPS+': player_data.get('OPS+', 0),
            }
            writer.writerow(row)

def update_rankings():
    print("🔄 Fetching dynasty rankings from multiple sources...")

    sources = [
        fetch_razzball_hitters,
        fetch_razzball_pitchers,
        fetch_fantasypros_hitters,
        fetch_fantasypros_pitchers,
        fetch_hashtagbaseball,
    ]

    dfs = []
    for source_func in sources:
        try:
            df = source_func()
            if not df.empty:
                dfs.append(df)
            else:
                print(f"Warning: {source_func.__name__} returned empty dataframe.")
        except Exception as e:
            print(f"Warning: Exception while fetching from {source_func.__name__}: {e}")

    print("📊 Combining rankings...")
    combined = combine_rankings(dfs)

    print("📈 Fetching advanced stats...")
    advanced_stats = {}
    try:
        advanced_stats = fetch_statcast_advanced()
    except Exception as e:
        print(f"Warning: Exception while fetching advanced stats: {e}")

    # Merge advanced stats into combined
    for player_name in combined:
        key = player_name.lower()
        adv = advanced_stats.get(key, {})
        combined[player_name].update({
            'WAR': adv.get('WAR', 0),
            'OPS': adv.get('OPS', 0),
            'SLG': adv.get('SLG', 0),
            'OPS+': adv.get('OPS+', 0),
            'dynasty_value': adv.get('dynasty_value', 0),
        })

    print("💾 Saving combined rankings with advanced stats to dynasty_rankings.csv...")
    write_csv(combined)
    print("✅ Rankings updated successfully!")

if __name__ == "__main__":
    update_rankings()