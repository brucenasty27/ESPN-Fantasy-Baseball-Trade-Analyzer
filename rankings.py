import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import time

# URLs for data sources
RAZZBALL_HITTERS_URL = "https://razzball.com/mlbhittingstats/"
RAZZBALL_PITCHERS_URL = "https://razzball.com/mlbpitchingstats/"
FANTASYPROS_HITTERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"
FANTASYPROS_PITCHERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"
HASHTAG_BASEBALL_URL = "https://hashtagbaseball.com/fantasy-baseball-rankings"
STATCAST_ADVANCED_URL = "https://baseballsavant.mlb.com/leaderboard/dynasty?type=hitting"

def clean_player_name(name):
    """Normalize player name for consistent matching."""
    if not isinstance(name, str):
        return ""
    # Remove suffixes, parentheses, whitespace, and lowercase
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_razzball_hitters():
    try:
        tables = pd.read_html(RAZZBALL_HITTERS_URL)
        df = tables[0]
        df['name'] = df['Player'].apply(clean_player_name)
        df['overall_rank'] = df['Rank']
        df['pos_rank'] = df['PosRank']
        df['position'] = df['Pos']
        return df[['name', 'overall_rank', 'pos_rank', 'position']]
    except Exception as e:
        print(f"Warning: Failed to fetch Razzball hitters: {e}")
        return pd.DataFrame()

def fetch_razzball_pitchers():
    try:
        tables = pd.read_html(RAZZBALL_PITCHERS_URL)
        df = tables[0]
        df['name'] = df['Player'].apply(clean_player_name)
        df['overall_rank'] = df['Rank']
        df['pos_rank'] = df['PosRank']
        df['position'] = df['Pos']
        return df[['name', 'overall_rank', 'pos_rank', 'position']]
    except Exception as e:
        print(f"Warning: Failed to fetch Razzball pitchers: {e}")
        return pd.DataFrame()

def fetch_fantasypros_hitters():
    try:
        tables = pd.read_html(FANTASYPROS_HITTERS_URL)
        df = tables[0]
        df['name'] = df['Player'].apply(clean_player_name)
        df['overall_rank'] = df.index + 1
        df['pos_rank'] = 0  # No positional rank on FP for now
        df['position'] = df['POS'] if 'POS' in df.columns else ''
        return df[['name', 'overall_rank', 'pos_rank', 'position']]
    except Exception as e:
        print(f"Warning: Failed to fetch FantasyPros hitters: {e}")
        return pd.DataFrame()

def fetch_fantasypros_pitchers():
    try:
        tables = pd.read_html(FANTASYPROS_PITCHERS_URL)
        df = tables[0]
        df['name'] = df['Player'].apply(clean_player_name)
        df['overall_rank'] = df.index + 1
        df['pos_rank'] = 0
        df['position'] = df['POS'] if 'POS' in df.columns else ''
        return df[['name', 'overall_rank', 'pos_rank', 'position']]
    except Exception as e:
        print(f"Warning: Failed to fetch FantasyPros pitchers: {e}")
        return pd.DataFrame()

def fetch_hashtagbaseball():
    try:
        tables = pd.read_html(HASHTAG_BASEBALL_URL)
        df = tables[0]
        df['name'] = df['Player'].apply(clean_player_name)
        df['overall_rank'] = df.index + 1
        df['pos_rank'] = 0
        df['position'] = df['POS'] if 'POS' in df.columns else ''
        return df[['name', 'overall_rank', 'pos_rank', 'position']]
    except Exception as e:
        print(f"Warning: Failed to fetch Hashtag Baseball rankings: {e}")
        return pd.DataFrame()

def combine_rankings(dfs):
    """
    Combine multiple DataFrames by averaging ranks for matching players.
    Returns a dict keyed by player name with averaged ranks and positions.
    """
    combined = {}

    for df in dfs:
        if df.empty:
            continue
        for _, row in df.iterrows():
            name = row['name']
            if name not in combined:
                combined[name] = {
                    'overall_rank': 0,
                    'pos_rank': 0,
                    'position': row.get('position', ''),
                    'count': 0
                }
            combined[name]['overall_rank'] += row['overall_rank']
            combined[name]['pos_rank'] += row['pos_rank']
            combined[name]['count'] += 1

    # Average ranks
    for name in combined:
        count = combined[name]['count']
        if count > 0:
            combined[name]['overall_rank'] /= count
            combined[name]['pos_rank'] /= count

    return combined

def fetch_statcast_advanced():
    """
    Fetch advanced stats (WAR, OPS, SLG, OPS+) from Baseball Savant or fallback.
    Returns dict keyed by player name with stat dict.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0; +https://yourdomain.com)"
    }

    stats = {}

    try:
        resp = requests.get(STATCAST_ADVANCED_URL, headers=headers, timeout=10)
        resp.raise_for_status()

        # Parse HTML table since JSON API may not be available
        if "text/html" in resp.headers.get("Content-Type", ""):
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if not table:
                raise RuntimeError("Advanced stats table not found")

            headers_row = [th.get_text(strip=True) for th in table.find_all("th")]
            col_map = {}
            for idx, col in enumerate(headers_row):
                col_lower = col.lower()
                if "player" in col_lower:
                    col_map["player"] = idx
                elif "war" in col_lower:
                    col_map["WAR"] = idx
                elif col_lower == "ops":
                    col_map["OPS"] = idx
                elif col_lower == "ops+":
                    col_map["OPS+"] = idx
                elif "slg" in col_lower:
                    col_map["SLG"] = idx

            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) < len(headers_row):
                    continue

                name_raw = cells[col_map["player"]].get_text(strip=True)
                name = clean_player_name(name_raw)

                def parse_float(val):
                    try:
                        return float(val)
                    except:
                        return 0.0

                stat_war = parse_float(cells[col_map.get("WAR", -1)].get_text()) if col_map.get("WAR", -1) >= 0 else 0.0
                stat_ops = parse_float(cells[col_map.get("OPS", -1)].get_text()) if col_map.get("OPS", -1) >= 0 else 0.0
                stat_ops_plus = parse_float(cells[col_map.get("OPS+", -1)].get_text()) if col_map.get("OPS+", -1) >= 0 else 0.0
                stat_slg = parse_float(cells[col_map.get("SLG", -1)].get_text()) if col_map.get("SLG", -1) >= 0 else 0.0

                stats[name] = {
                    "WAR": stat_war,
                    "OPS": stat_ops,
                    "SLG": stat_slg,
                    "OPS+": stat_ops_plus,
                    "dynasty_value": 0,  # Placeholder for later computed value
                }

        else:
            print("Warning: Unsupported Content-Type for advanced stats")
            return {}

    except Exception as e:
        print(f"Warning: Failed to fetch advanced stats: {e}")
        return {}

    return stats

def merge_advanced_stats(combined_rankings, advanced_stats):
    """
    Merge advanced stats into combined rankings dict.
    """
    for player_name, stats in combined_rankings.items():
        adv = advanced_stats.get(player_name, {})
        for key in ["WAR", "OPS", "SLG", "OPS+"]:
            stats[key] = adv.get(key, 0.0)
        # dynasty_value can be calculated later or left as 0 for now
        stats["dynasty_value"] = 0
    return combined_rankings

def export_combined_rankings_to_csv(combined_rankings, filename="dynasty_rankings_cleaned.csv"):
    """
    Export the combined rankings dictionary to a CSV file.
    """
    rows = []
    for name, stats in combined_rankings.items():
        row = {
            "name": name,
            "overall_rank": stats.get("overall_rank", 0),
            "pos_rank": stats.get("pos_rank", 0),
            "position": stats.get("position", ""),
            "WAR": stats.get("WAR", 0),
            "OPS": stats.get("OPS", 0),
            "SLG": stats.get("SLG", 0),
            "OPS+": stats.get("OPS+", 0),
            "dynasty_value": stats.get("dynasty_value", 0),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"Saved combined rankings to {filename}")

