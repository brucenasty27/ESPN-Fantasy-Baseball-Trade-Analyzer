import pandas as pd
import requests
import re
from bs4 import BeautifulSoup

# URLs for sources
RAZZBALL_HITTERS_URL = "https://razzball.com/mlbhittingstats/"
RAZZBALL_PITCHERS_URL = "https://razzball.com/mlbpitchingstats/"
FANTASYPROS_HITTERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"
FANTASYPROS_PITCHERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"
HASHTAG_BASEBALL_URL = "https://hashtagbaseball.com/dynasty-rankings"
STATCAST_ADVANCED_URL = "https://baseballsavant.mlb.com/leaderboard/dynasty?type=hitting"

def clean_player_name(name):
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_html_table(url, name_col="Player", pos_col="POS", rank_offset=1):
    try:
        df = pd.read_html(url)[0]
        df["name"] = df[name_col].apply(clean_player_name)
        df["overall_rank"] = df.index + rank_offset
        df["pos_rank"] = 0
        df["position"] = df[pos_col] if pos_col in df.columns else ""
        return df[["name", "overall_rank", "pos_rank", "position"]]
    except Exception as e:
        print(f"Warning: Failed to fetch from {url}: {e}")
        return pd.DataFrame()

def fetch_all_rankings():
    dfs = [
        fetch_html_table(RAZZBALL_HITTERS_URL),
        fetch_html_table(RAZZBALL_PITCHERS_URL),
        fetch_html_table(FANTASYPROS_HITTERS_URL),
        fetch_html_table(FANTASYPROS_PITCHERS_URL),
        fetch_html_table(HASHTAG_BASEBALL_URL)
    ]
    return dfs

def combine_rankings(dfs):
    combined = {}
    for df in dfs:
        if df.empty:
            continue
        for _, row in df.iterrows():
            name = row["name"]
            if name not in combined:
                combined[name] = {
                    "overall_rank": 0,
                    "pos_rank": 0,
                    "position": row.get("position", ""),
                    "count": 0
                }
            combined[name]["overall_rank"] += row["overall_rank"]
            combined[name]["pos_rank"] += row["pos_rank"]
            combined[name]["count"] += 1
    for name in combined:
        combined[name]["overall_rank"] /= combined[name]["count"]
        combined[name]["pos_rank"] /= combined[name]["count"]
    return combined

def fetch_statcast_advanced():
    stats = {}
    try:
        resp = requests.get(STATCAST_ADVANCED_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            return stats

        headers_row = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        col_map = {name: i for i, name in enumerate(headers_row)}

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if not cells or len(cells) < len(headers_row):
                continue

            name = clean_player_name(cells[col_map["player"]].get_text())
            stats[name] = {
                "WAR": safe_float(cells[col_map.get("war", -1)].get_text()),
                "OPS": safe_float(cells[col_map.get("ops", -1)].get_text()),
                "SLG": safe_float(cells[col_map.get("slg", -1)].get_text()),
                "OPS+": safe_float(cells[col_map.get("ops+", -1)].get_text()),
            }
    except Exception as e:
        print(f"Warning: Failed to fetch advanced stats: {e}")
    return stats

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

def build_combined_dataframe():
    dfs = fetch_all_rankings()
    combined = combine_rankings(dfs)
    advanced_stats = fetch_statcast_advanced()

    data = []
    for name, vals in combined.items():
        adv = advanced_stats.get(name, {})
        data.append({
            "name": name,
            "overall_rank": round(vals["overall_rank"], 2),
            "pos_rank": round(vals["pos_rank"], 2),
            "position": vals["position"],
            "WAR": adv.get("WAR", 0),
            "OPS": adv.get("OPS", 0),
            "SLG": adv.get("SLG", 0),
            "OPS+": adv.get("OPS+", 0),
            "dynasty_value": round(1000 / (1 + vals["overall_rank"]), 2)
        })
    return pd.DataFrame(data)

if __name__ == "__main__":
    final_df = build_combined_dataframe()
    final_df.to_csv("dynasty_rankings.csv", index=False)
    print("✅ Dynasty rankings saved to dynasty_rankings.csv")
