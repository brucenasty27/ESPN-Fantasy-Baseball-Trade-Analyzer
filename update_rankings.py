import csv
import re
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

def clean_player_name(name):
    """Normalize player name for matching."""
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def write_csv(players_dict, filename='dynasty_rankings.csv'):
    """
    Write combined rankings with advanced stats to CSV.
    """
    fieldnames = [
        "name", "overall_rank", "pos_rank", "position",
        "dynasty_value", "WAR", "OPS", "SLG", "OPS+"
    ]
    with open(filename, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for player in players_dict.values():
            writer.writerow(player)

def update_rankings():
    print("🔄 Fetching dynasty rankings from multiple sources...")
    legacy_dfs = [
        fetch_razzball_hitters(),
        fetch_razzball_pitchers(),
        fetch_fantasypros_hitters(),
        fetch_fantasypros_pitchers(),
        fetch_hashtagbaseball(),
    ]

    print("📊 Combining rankings...")
    combined = combine_rankings(legacy_dfs)

    print("📈 Fetching advanced stats...")
    advanced_stats = fetch_statcast_advanced()

    print("🔀 Merging with advanced stats...")
    merged = {}
    for player_name, data in combined.items():
        key = clean_player_name(player_name)
        adv = advanced_stats.get(key, {})

        merged[player_name] = {
            "name": player_name,
            "overall_rank": data.get("overall_rank", 9999),
            "pos_rank": data.get("position_rank", 9999),
            "position": data.get("position", ""),
            "dynasty_value": adv.get("dynasty_value", 0),
            "WAR": adv.get("WAR", 0),
            "OPS": adv.get("OPS", 0),
            "SLG": adv.get("SLG", 0),
            "OPS+": adv.get("OPS+", 0),
        }

    print("💾 Writing to dynasty_rankings.csv...")
    write_csv(merged)
    print("✅ Dynasty rankings updated successfully.")

if __name__ == "__main__":
    update_rankings()
