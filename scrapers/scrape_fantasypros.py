import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
HITTERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"
PITCHERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"

def clean_name(name):
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def scrape_fantasypros_table(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch {url} (status {response.status_code})")

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"id": "data"})
    if not table:
        raise ValueError(f"Could not find rankings table on {url}")

    df = pd.read_html(str(table))[0]
    return df

def find_pos_rank_column(df):
    # Look for a column header containing "pos rank" or similar, case-insensitive
    for col in df.columns:
        if isinstance(col, str) and "pos rank" in col.lower():
            return col
    return None

def fetch_fantasypros_hitters(save_csv=False):
    try:
        print("Scraping FantasyPros dynasty hitters...")
        df = scrape_fantasypros_table(HITTERS_URL)
        df.rename(columns={"Player Name": "name", "Rank": "overall_rank"}, inplace=True)
        df["name"] = df["name"].apply(clean_name)
        df["overall_rank"] = pd.to_numeric(df["overall_rank"], errors="coerce")

        # Detect positional rank column
        pos_rank_col = find_pos_rank_column(df)
        if pos_rank_col:
            df["pos_rank"] = pd.to_numeric(df[pos_rank_col], errors="coerce").fillna(0).astype(int)
        else:
            df["pos_rank"] = 0

        # Stats to include for hitters
        stat_map = {
            "HR": "HR",
            "R": "R",
            "RBI": "RBI",
            "SB": "SB",
            "BB": "BB",
            "AVG": "AVG",
        }
        # Add missing stat columns with 0
        for col in stat_map:
            if col in df.columns:
                df.rename(columns={col: stat_map[col]}, inplace=True)
            else:
                df[stat_map[col]] = 0

        df["position"] = df["POS"] if "POS" in df.columns else "H"

        cols = ["name", "overall_rank", "pos_rank", "position"] + list(stat_map.values())
        df = df[cols].dropna(subset=["name", "overall_rank"])

        if save_csv:
            df.to_csv("fantasypros_hitters_rankings.csv", index=False)
            print("✅ Saved FantasyPros hitters to fantasypros_hitters_rankings.csv")
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch FantasyPros hitters: {e}")
        return pd.DataFrame()

def fetch_fantasypros_pitchers(save_csv=False):
    try:
        print("Scraping FantasyPros dynasty pitchers...")
        df = scrape_fantasypros_table(PITCHERS_URL)
        df.rename(columns={"Player Name": "name", "Rank": "overall_rank"}, inplace=True)
        df["name"] = df["name"].apply(clean_name)
        df["overall_rank"] = pd.to_numeric(df["overall_rank"], errors="coerce")

        # Detect positional rank column
        pos_rank_col = find_pos_rank_column(df)
        if pos_rank_col:
            df["pos_rank"] = pd.to_numeric(df[pos_rank_col], errors="coerce").fillna(0).astype(int)
        else:
            df["pos_rank"] = 0

        # Stats to include for pitchers
        stat_map = {
            "W": "W",
            "SV": "SV",
            "K": "K",
            "ERA": "ERA",
            "WHIP": "WHIP",
        }
        for col in stat_map:
            if col in df.columns:
                df.rename(columns={col: stat_map[col]}, inplace=True)
            else:
                df[stat_map[col]] = 0

        df["position"] = df["POS"] if "POS" in df.columns else "P"

        cols = ["name", "overall_rank", "pos_rank", "position"] + list(stat_map.values())
        df = df[cols].dropna(subset=["name", "overall_rank"])

        if save_csv:
            df.to_csv("fantasypros_pitchers_rankings.csv", index=False)
            print("✅ Saved FantasyPros pitchers to fantasypros_pitchers_rankings.csv")
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch FantasyPros pitchers: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Standalone run: scrape both and save to CSV
    hitters = fetch_fantasypros_hitters(save_csv=True)
    time.sleep(1)  # polite delay
    pitchers = fetch_fantasypros_pitchers(save_csv=True)

    combined = pd.concat([hitters, pitchers], ignore_index=True)
    combined.to_csv("fantasypros_combined_rankings.csv", index=False)
    print(f"✅ Saved combined FantasyPros rankings ({len(combined)}) players to fantasypros_combined_rankings.csv")
