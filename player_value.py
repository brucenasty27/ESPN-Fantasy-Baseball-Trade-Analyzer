# player_value.py

import pandas as pd

RANKINGS_FILE = "dynasty_rankings.csv"

def load_rankings():
    try:
        df = pd.read_csv(RANKINGS_FILE)
        df.fillna(0, inplace=True)
        df["player_name_lower"] = df["player_name"].str.lower()
        return df
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame(columns=["player_name", "dynasty_value", "overall_rank", "position_rank", "WAR", "OPS", "SLG", "OPS+"])


rankings_df = load_rankings()

def get_dynasty_value(player):
    if not player or not hasattr(player, 'name'):
        return 0
    name = player.name.lower()
    match = rankings_df[rankings_df["player_name_lower"] == name]
    if not match.empty:
        return float(match.iloc[0]["dynasty_value"])
    return 0

def get_simple_draft_pick_value(pick):
    # Simple declining pick value curve from 100 (1.01) to ~1 (16.10)
    pick_num = (pick.round_number - 1) * 10 + 1  # assume 10 picks per round
    return max(1, 100 - (pick_num - 1) * 0.6)  # Adjust decay as needed

def get_player_ranks(name):
    if not name:
        return {}
    match = rankings_df[rankings_df["player_name_lower"] == name.lower()]
    if match.empty:
        return {}
    row = match.iloc[0]
    return {
        "Dynasty Value": row.get("dynasty_value", 0),
        "Overall Rank": int(row.get("overall_rank", 9999)),
        "Position Rank": int(row.get("position_rank", 9999)),
        "WAR": row.get("WAR", 0),
        "OPS": row.get("OPS", 0),
        "SLG": row.get("SLG", 0),
        "OPS+": row.get("OPS+", 0)
    }
