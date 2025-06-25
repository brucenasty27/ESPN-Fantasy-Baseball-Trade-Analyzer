import pandas as pd
import os
from scrapers.scrape_espn_hitters import fetch_espn_hitters
from scrapers.scrape_fangraphs_pitchers import fetch_fangraphs_pitchers

RANKINGS_FILE = os.path.join("data", "dynasty_rankings_cleaned.csv")

# Helper function to safely parse IP (e.g. 45.2 innings = 45 + 2/3)
def parse_ip(ip_val):
    try:
        ip_float = float(ip_val)
        whole = int(ip_float)
        fraction = round(ip_float - whole, 1)
        if fraction == 0.1:
            return whole + 1/3
        elif fraction == 0.2:
            return whole + 2/3
        return ip_float
    except:
        return 0.0

def fetch_all_sources():
    hitters = fetch_espn_hitters()
    pitchers = fetch_fangraphs_pitchers()

    if pitchers is not None and "IP" in pitchers.columns:
        pitchers["IP"] = pitchers["IP"].apply(parse_ip)

    combined = pd.concat([hitters, pitchers], ignore_index=True, sort=False).fillna(0)

    combined["dynasty_value"] = combined.apply(lambda row: dynasty_value_pitcher(row) if row["position"] in ["SP", "RP", "P"] else dynasty_value_hitter(row), axis=1)

    # Fill default ranks if not present
    if "overall_rank" not in combined:
        combined["overall_rank"] = 9999
    if "pos_rank" not in combined:
        combined["pos_rank"] = 9999

    combined = combined[[
        "name", "dynasty_value", "overall_rank", "pos_rank", "position",
        "WAR", "OPS", "SLG", "OPS+",
        "HR", "R", "RBI", "SB", "AVG", "BB",
        "W", "SV", "K", "ERA", "WHIP", "IP"
    ]].copy()

    combined.to_csv(RANKINGS_FILE, index=False)
    return combined

def load_rankings():
    if not os.path.exists(RANKINGS_FILE):
        print(f"⚠️ Rankings file not found at {RANKINGS_FILE}")
        return pd.DataFrame(columns=[
            "name", "dynasty_value", "overall_rank", "pos_rank",
            "WAR", "OPS", "SLG", "OPS+",
            "HR", "R", "RBI", "SB", "AVG", "BB",
            "W", "SV", "K", "ERA", "WHIP", "IP",
            "position"
        ])
    try:
        df = pd.read_csv(RANKINGS_FILE)
        df.fillna(0, inplace=True)
        df["name"] = df["name"].astype(str).str.strip().str.lower()
        df["position"] = df["position"].astype(str).str.upper()
        df["IP"] = df["IP"].apply(parse_ip)
        return df
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame(columns=[
            "name", "dynasty_value", "overall_rank", "pos_rank",
            "WAR", "OPS", "SLG", "OPS+",
            "HR", "R", "RBI", "SB", "AVG", "BB",
            "W", "SV", "K", "ERA", "WHIP", "IP",
            "position"
        ])

rankings_df = load_rankings()

def dynasty_value_hitter(stats):
    return round(
        stats.get("HR", 0) * 4.0 +
        stats.get("R", 0) * 1.0 +
        stats.get("RBI", 0) * 1.0 +
        stats.get("SB", 0) * 2.0 +
        stats.get("AVG", 0) * 50.0 +
        stats.get("BB", 0) * 1.0,
        2
    )

def dynasty_value_pitcher(stats):
    era = stats.get("ERA", 4.0)
    whip = stats.get("WHIP", 1.3)
    era_score = max(0, 4.0 - era) * 20.0
    whip_score = max(0, 1.3 - whip) * 30.0

    return round(
        stats.get("W", 0) * 5.0 +
        stats.get("SV", 0) * 5.0 +
        stats.get("K", 0) * 1.0 +
        era_score +
        whip_score +
        stats.get("IP", 0) * 0.5,
        2
    )

def get_dynasty_value(player_name):
    if not player_name:
        return 0
    if hasattr(player_name, 'name'):
        player_name = player_name.name

    name = str(player_name).strip().lower()
    match = rankings_df[rankings_df["name"] == name]
    if match.empty:
        return 0

    row = match.iloc[0]

    stats = {
        "HR": row.get("HR", 0),
        "R": row.get("R", 0),
        "RBI": row.get("RBI", 0),
        "SB": row.get("SB", 0),
        "AVG": row.get("AVG", 0),
        "BB": row.get("BB", 0),
        "W": row.get("W", 0),
        "SV": row.get("SV", 0),
        "K": row.get("K", 0),
        "ERA": row.get("ERA", 4.0),
        "WHIP": row.get("WHIP", 1.3),
        "IP": parse_ip(row.get("IP", 0))
    }

    position = str(row.get("position", "")).upper()
    if position in {"SP", "RP", "P"}:
        return dynasty_value_pitcher(stats)
    else:
        return dynasty_value_hitter(stats)

def get_simple_draft_pick_value(pick):
    pick_num = (pick.round_number - 1) * 10 + 1
    return max(1, 100 - (pick_num - 1) * 0.6)

def get_player_ranks(name):
    if not name:
        return {}
    name = str(name).strip().lower()
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
        "OPS+": float(row.get("OPS+", 0)),
    }
