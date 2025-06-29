import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

URL = "https://www.fangraphs.com/fantasy-tools/player-rater?leaguetype=1&pos=&posType=bat"

def clean_name(name):
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_fangraphs_hitters():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {URL} (status {response.status_code})")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", id="LeaderBoard1_dg1_ctl") or \
            soup.find("table", id="LeaderBoard1_dg1") or \
            soup.find("table")

    if not table:
        print("Could not find player ratings table on FanGraphs page")
        return pd.DataFrame()

    thead = table.find("thead")
    if not thead:
        print("No <thead> found in table")
        return pd.DataFrame()

    headers_row = [th.get_text(strip=True).lower() for th in thead.find_all("th")]

    rows = []
    tbody = table.find("tbody")
    if not tbody:
        print("No <tbody> found in table")
        return pd.DataFrame()

    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if not cells or len(cells) != len(headers_row):
            continue
        row_data = {}
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            # Clean player name if appropriate
            if i == 1 or 'player' in headers_row[i]:
                a = cell.find("a")
                if a:
                    text = a.get_text(strip=True)
                text = clean_name(text)
            row_data[headers_row[i]] = text
        rows.append(row_data)

    df = pd.DataFrame(rows)

    # Lowercase all columns for consistent mapping
    df.columns = [col.lower() for col in df.columns]

    col_map = {
        'player': 'name',
        'pos': 'position',
        'rank': 'overall_rank',
        'r': 'R',
        'hr': 'HR',
        'rbi': 'RBI',
        'sb': 'SB',
        'avg': 'AVG',
        'bb': 'BB',
    }

    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    # Ensure required columns exist with default values
    for col in ['overall_rank', 'pos_rank', 'position', 'R', 'HR', 'RBI', 'SB', 'AVG', 'BB']:
        if col not in df.columns:
            df[col] = 0 if col != 'position' else ''

    # Convert numeric columns
    numeric_cols = ['overall_rank', 'pos_rank', 'R', 'HR', 'RBI', 'SB', 'AVG', 'BB']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Optional: convert position to uppercase for consistency downstream
    df['position'] = df['position'].str.upper()

    # Return relevant columns, in consistent order
    return df[['name', 'overall_rank', 'pos_rank', 'position', 'R', 'HR', 'RBI', 'SB', 'AVG', 'BB']]

if __name__ == "__main__":
    df = fetch_fangraphs_hitters()
    print(f"Fetched {len(df)} hitters from FanGraphs")
    df.to_csv("data/fangraphs_hitters.csv", index=False)
