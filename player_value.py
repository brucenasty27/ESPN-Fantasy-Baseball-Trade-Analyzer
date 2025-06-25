import pandas as pd
import os
import re

RANKINGS_FILE = os.path.join("data", "dynasty_rankings_cleaned.csv")

def parse_ip(ip_str):
    """
    Parse innings pitched from string format to decimal float.
    MLB IP format example: "50.2" means 50 innings + 2 outs (2/3 inning).
    Convert "50.2" to 50 + 2/3 = 50.6667
    """
    if pd.isna(ip_str):
        return 0.0
    if isinstance(ip_str, (int, float)):
        return float(ip_str)
    ip_str = str(ip_str).strip()
    match = re.match(r"^(\d+)(?:\.(\d))?$", ip_str)
    if not match:
        return 0.0
    innings = int(match.group(1))
    outs = int(match.group(2)) if match.group(2) else 0
    if outs > 2:
        # Invalid outs count for innings pitched, fallback
        return float(innings)
    return innings + outs / 3.0

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

        # Normalize player names for matching
        df["name"] = df["name"].astype(str).str.strip().str.lower()
        df["position"] = df["position"].astype(str).str.upper()

        # Parse IP column properly into decimal format
        if "IP" in df.columns:
            df["IP"] = df["IP"].apply(parse_ip)
        else:
            df["IP"] = 0.0

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

def dynasty_value_hitter(stats: dict) -> float:
    hr = stats.get("HR", 0)
    r = stats.get("R", 0)
    rbi = stats.get("RBI", 0)
    sb = stats.get("SB", 0)
    avg = stats.get("AVG", 0)
    bb = stats.get("BB", 0)

    value = (
        hr * 4.0 +
        r * 1.0 +
        rbi * 1.0 +
        sb * 2.0 +
        avg * 50.0 +  # scale batting average
        bb * 1.0
    )
    return round(value, 2)

def dynasty_value_pitcher(stats: dict) -> float:
    w = stats.get("W", 0)
    sv = stats.get("SV", 0)
    k = stats.get("K", 0)
    era = stats.get("ERA", 4.0)  # average baseline ERA
    whip = stats.get("WHIP", 1.3)  # average baseline WHIP
    ip = stats.get("IP", 0.0)

    era_score = max(0, 4.0 - era) * 20.0
    whip_score = max(0, 1.3 - whip) * 30.0

    value = (
        w * 5.0 +
        sv * 5.0 +
        k * 1.0 +
        era_score +
        whip_score +
        ip * 0.5
    )
    return round(value, 2)

def get_dynasty_value(player_name) -> float:
    """
    Lookup player in rankings_df, extract ESPN-style stats,
    determine position, and compute dynasty value accordingly.
    """
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
        # Hitters stats
        "HR": row.get("HR", 0),
        "R": row.get("R", 0),
        "RBI": row.get("RBI", 0),
        "SB": row.get("SB", 0),
        "AVG": row.get("AVG", 0),
        "BB": row.get("BB", 0),

        # Pitchers stats
        "W": row.get("W", 0),
        "SV": row.get("SV", 0),
        "K": row.get("K", 0),
        "ERA": row.get("ERA", 4.0),
        "WHIP": row.get("WHIP", 1.3),
        "IP": row.get("IP", 0.0),
    }

    position = str(row.get("position", "")).upper()

    pitcher_positions = {"SP", "RP", "P"}
    if position in pitcher_positions:
        return dynasty_value_pitcher(stats)
    else:
        return dynasty_value_hitter(stats)

def get_simple_draft_pick_value(pick):
    # Assuming 10 picks per round in your league
    pick_num = (pick.round_number - 1) * 10 + 1
    # Basic linear depreciation curve for draft picks
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
