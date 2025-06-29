import pandas as pd
import os
from scrapers.scrape_espn_stats import fetch_espn_hitter_stats, fetch_espn_pitcher_stats
from scrapers.scrape_fangraphs_pitchers import fetch_fangraphs_pitchers
from scrapers.scrape_fangraphs_hitters import fetch_fangraphs_hitters

RANKINGS_FILE = os.path.join("data", "dynasty_rankings_cleaned.csv")

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

def fetch_all_sources(league):
    # Fetch ESPN hitters
    try:
        hitters_espn = fetch_espn_hitter_stats(league)
    except Exception as e:
        print(f"Error fetching ESPN hitters: {e}")
        hitters_espn = pd.DataFrame()

    # Fetch ESPN pitchers
    try:
        pitchers_espn = fetch_espn_pitcher_stats(league)
    except Exception as e:
        print(f"Error fetching ESPN pitchers: {e}")
        pitchers_espn = pd.DataFrame()

    if pitchers_espn is not None and "IP" in pitchers_espn.columns:
        pitchers_espn["IP"] = pitchers_espn["IP"].apply(parse_ip)

    # Fetch Fangraphs hitters
    try:
        hitters_fg = fetch_fangraphs_hitters()
    except Exception as e:
        print(f"Error fetching Fangraphs hitters: {e}")
        hitters_fg = pd.DataFrame()

    # Fetch Fangraphs pitchers
    try:
        pitchers_fg = fetch_fangraphs_pitchers()
    except Exception as e:
        print(f"Error fetching Fangraphs pitchers: {e}")
        pitchers_fg = pd.DataFrame()

    if pitchers_fg is not None and "IP" in pitchers_fg.columns:
        pitchers_fg["IP"] = pitchers_fg["IP"].apply(parse_ip)

    return [hitters_espn, pitchers_espn, hitters_fg, pitchers_fg]

def combine_rankings(dfs):
    """
    Combine multiple DataFrames of player rankings/stats into a single cleaned DataFrame.
    """

    # Filter out empty or None DataFrames
    valid_dfs = [df for df in dfs if df is not None and not df.empty]

    if not valid_dfs:
        return pd.DataFrame()  # Return empty DataFrame if no valid data

    # Concatenate all valid DataFrames
    combined = pd.concat(valid_dfs, ignore_index=True, sort=False)

    # Clean player names
    combined["name"] = combined["name"].astype(str).str.strip().str.lower()

    # Normalize position strings to uppercase and fill missing with empty string
    combined["position"] = combined.get("position", "").astype(str).str.upper().fillna("")

    # Parse IP for pitchers if exists
    if "IP" in combined.columns:
        combined["IP"] = combined["IP"].apply(parse_ip)

    # Fill missing numeric values with 0
    combined.fillna(0, inplace=True)

    # Calculate dynasty_value for each row
    def calc_dyn_val(row):
        pos = row.get("position", "")
        if pos in {"SP", "RP", "P"}:
            return dynasty_value_pitcher(row)
        else:
            return dynasty_value_hitter(row)

    combined["dynasty_value"] = combined.apply(calc_dyn_val, axis=1)

    # Ensure default ranks exist
    if "overall_rank" not in combined.columns:
        combined["overall_rank"] = 9999
    if "pos_rank" not in combined.columns:
        combined["pos_rank"] = 9999

    # Define expected columns and add missing with zeros
    expected_cols = [
        "name", "dynasty_value", "overall_rank", "pos_rank", "position",
        "WAR", "OPS", "SLG", "OPS+",
        "HR", "R", "RBI", "SB", "AVG", "BB",
        "W", "SV", "K", "ERA", "WHIP", "IP"
    ]
    for col in expected_cols:
        if col not in combined.columns:
            combined[col] = 0

    # Return combined DataFrame with columns in expected order
    combined = combined[expected_cols].copy()

    # Save combined rankings to file
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
