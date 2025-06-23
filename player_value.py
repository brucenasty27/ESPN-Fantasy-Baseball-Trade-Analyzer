# player_value.py

import pandas as pd

RANKINGS_FILE = "dynasty_rankings_cleaned.csv"

def load_rankings():
    try:
        df = pd.read_csv(RANKINGS_FILE)
        df.fillna(0, inplace=True)
        df["name"] = df["name"].str.strip().str.lower()
        return df
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame(columns=[
            "name", "dynasty_value", "overall_rank", "pos_rank", 
            "WAR", "OPS", "SLG", "OPS+"
        ])

rankings_df = load_rankings()

def get_dynasty_value(player_name):
    if not player_name:
        return 0
    if hasattr(player_name, 'name'):  # in case a player object is passed
        player_name = player_name.name
    name = player_name.strip().lower()
    match = rankings_df[rankings_df["name"] == name]
    if not match.empty:
        return float(match.iloc[0].get("dynasty_value", 0))
    return 0

def get_simple_draft_pick_value(pick):
    """
    Basic linear decline model for pick valuation.
    Assumes 10 picks per round, values decay from 100 down.
    """
    pick_num = (pick.round_number - 1) * 10 + 1  # first pick of round
    return max(1, 100 - (pick_num - 1) * 0.6)

def get_player_ranks(name):
    if not name:
        return {}
    name = name.strip().lower()
    match = rankings_df[rankings_df["name"] == name]
    if match.empty:
        return {}
    row = match.iloc[0]
    return {
        "Dynasty Value": float(row.get("dynasty_value", 0)),
        "Overall Rank": int(row.get("overall_rank", 9999)),
        "Position Rank": int(row.get("pos_rank", 9999)),
        "WAR": float(row.get("WAR", 0)),
        "OPS": float(row.get("OPS", 0)),
        "SLG": float(row.get("SLG", 0)),
        "OPS+": float(row.get("OPS+", 0))
    }
