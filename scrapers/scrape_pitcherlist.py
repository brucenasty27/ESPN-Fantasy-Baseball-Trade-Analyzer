import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.pitcherlist.com/category/dynasty/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0)"
}

def clean_player_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_pitcherlist_rankings():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the first table that likely contains rankings
        table = soup.find("table")
        if not table:
            raise RuntimeError("PitcherList rankings table not found")

        rows = table.find_all("tr")[1:]  # skip header
        data = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            try:
                rank = int(cells[0].text.strip())
            except ValueError:
                rank = 0
            player_name = clean_player_name(cells[1].text.strip())
            position = cells[2].text.strip()

            data.append({
                "name": player_name,
                "overall_rank": rank,
                "pos_rank": 0,
                "position": position,
                # Add placeholders for stats expected downstream
                "WAR": 0,
                "ERA": 0,
                "WHIP": 0,
                "K_per_9": 0,
                "dynasty_value": 0
            })

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"Warning: Failed to fetch PitcherList rankings: {e}")
        return pd.DataFrame()

def integrate_rankings(*dataframes):
    """
    Combine multiple player ranking DataFrames into one unified DataFrame.

    Args:
        *dataframes: variable number of pd.DataFrame inputs, each with columns including
                     'name', 'overall_rank', 'position', and optionally stats like WAR, ERA, etc.

    Returns:
        pd.DataFrame: Combined, deduplicated DataFrame with best (lowest) overall_rank per player.
    """
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Normalize names
    combined_df['name'] = combined_df['name'].astype(str).str.strip().str.lower()

    # Sort by overall_rank ascending so best ranks are first
    combined_df = combined_df.sort_values(by='overall_rank')

    # Deduplicate by player name, keeping the first occurrence (best rank)
    combined_df = combined_df.drop_duplicates(subset=['name'], keep='first')

    # Fill missing numeric columns with zeros
    stat_cols = ['overall_rank', 'pos_rank', 'WAR', 'ERA', 'WHIP', 'K_per_9',
                 'HR', 'R', 'RBI', 'SB', 'BB', 'AVG', 'W', 'SV', 'K', 'OPS', 'SLG', 'OPS+']
    for col in stat_cols:
        if col in combined_df.columns:
            combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').fillna(0)
        else:
            combined_df[col] = 0

    # Ensure position column exists
    if 'position' not in combined_df.columns:
        combined_df['position'] = ''

    return combined_df.reset_index(drop=True)


if __name__ == "__main__":
    print("🔎 Fetching PitcherList rankings...")
    df_pitcherlist = fetch_pitcherlist_rankings()

    print("📥 Loading other rankings CSVs...")
    # Load other scrapers' CSVs if they exist; skip if not
    try:
        df_fantrax = pd.read_csv("fantraxhq_rankings.csv")
    except:
        print("⚠️ fantraxhq_rankings.csv not found, skipping")
        df_fantrax = pd.DataFrame()

    try:
        df_fantasypros = pd.read_csv("fantasypros_combined_rankings.csv")
    except:
        print("⚠️ fantasypros_combined_rankings.csv not found, skipping")
        df_fantasypros = pd.DataFrame()

    try:
        df_cbssports = pd.read_csv("data/cbssports_rankings.csv")
    except:
        print("⚠️ cbssports_rankings.csv not found, skipping")
        df_cbssports = pd.DataFrame()

    try:
        df_fangraphs_hitters = pd.read_csv("data/fangraphs_hitters.csv")
    except:
        print("⚠️ fangraphs_hitters.csv not found, skipping")
        df_fangraphs_hitters = pd.DataFrame()

    try:
        df_fangraphs_pitchers = pd.read_csv("data/fangraphs_pitchers.csv")
    except:
        print("⚠️ fangraphs_pitchers.csv not found, skipping")
        df_fangraphs_pitchers = pd.DataFrame()

    # Combine Fangraphs hitters and pitchers if available
    if not df_fangraphs_hitters.empty and not df_fangraphs_pitchers.empty:
        df_fangraphs = pd.concat([df_fangraphs_hitters, df_fangraphs_pitchers], ignore_index=True)
    else:
        df_fangraphs = pd.DataFrame()

    print("🔗 Integrating all rankings...")
    combined_rankings = integrate_rankings(
        df_pitcherlist,
        df_fantrax,
        df_fantasypros,
        df_cbssports,
        df_fangraphs
    )

    combined_rankings.to_csv("data/combined_dynasty_rankings.csv", index=False)
    print(f"✅ Saved combined dynasty rankings for {len(combined_rankings)} players to data/combined_dynasty_rankings.csv")
