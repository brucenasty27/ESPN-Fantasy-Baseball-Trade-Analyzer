import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import time

# URLs for sources
RAZZBALL_HITTERS_URL = "https://razzball.com/mlbhittingstats/"
RAZZBALL_PITCHERS_URL = "https://razzball.com/mlbpitchingstats/"
FANTASYPROS_HITTERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"
FANTASYPROS_PITCHERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"
HASHTAG_BASEBALL_URL = "https://hashtagbaseball.com/dynasty-rankings"
STATCAST_ADVANCED_URL = "https://baseballsavant.mlb.com/leaderboard/dynasty?type=hitting"

def clean_player_name(name):
    """Normalize player name for matching."""
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
        df['pos_rank'] = 0
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
    Returns dict keyed by player name.
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
        combined[name]['overall_rank'] /= combined[name]['count']
        combined[name]['pos_rank'] /= combined[name]['count']

    return combined

def fetch_statcast_advanced():
    """
    Fetch advanced stats (WAR, OPS, SLG, OPS+) from Baseball Savant or a fallback source.
    Returns a dict keyed by cleaned player names with stat dicts.
    Robust with error handling and retries.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0; +https://yourdomain.com)"
    }

    stats = {}

    try:
        # Baseball Savant JSON API endpoint example (adjust as needed)
        url = "https://baseballsavant.mlb.com/leaderboard/dynasty?type=hitting"

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # If response is HTML, parse table instead (common case)
        if "text/html" in resp.headers.get("Content-Type", ""):
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if not table:
                raise RuntimeError("Advanced stats table not found")

            headers_row = [th.get_text(strip=True) for th in table.find_all("th")]

            # Expected columns mapping - adjust if site changes
            col_map = {}
            for idx, col in enumerate(headers_row):
                col_lower = col.lower()
                if "player" in col_lower:
                    col_map["player"] = idx
                elif "war" in col_lower:
                    col_map["WAR"] = idx
                elif "ops" == col_lower or "ops+" in col_lower:
                    # handle ops and ops+ (assuming last columns)
                    if "ops+" in col_lower:
                        col_map["OPS+"] = idx
                    else:
                        col_map["OPS"] = idx
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
                stat_slg = parse_float(cells[col_map.get("SLG", -1)].get_text()) if col_map.get("SLG", -1) >= 0 else 0.0
                stat_ops_plus = parse_float(cells[col_map.get("OPS+", -1)].get_text()) if col_map.get("OPS+", -1) >= 0 else 0.0

                stats[name] = {
                    "WAR": stat_war,
                    "OPS": stat_ops,
                    "SLG": stat_slg,
                    "OPS+": stat_ops_plus,
                    # Dynasty value could be computed or default 0
                    "dynasty_value": 0,
                }

        else:
            # If API returns JSON, parse accordingly (placeholder)
            data_json = resp.json()
            # Implement parsing logic here if you switch to JSON source
            # For now fallback to empty
            print("Warning: JSON format not implemented, returning empty stats")
            return {}

    except Exception as e:
        print(f"Warning: Failed to fetch advanced stats from primary source: {e}")
        # Fallback strategy: return empty or implement another source here
        return {}

    return stats
