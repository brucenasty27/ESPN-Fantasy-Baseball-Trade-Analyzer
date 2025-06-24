import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

URL = "https://www.fangraphs.com/fantasy-tools/player-rater?leaguetype=1"

def clean_name(name):
    # Remove suffixes and trailing spaces
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def scrape_fangraphs_hitters():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {URL} (status {response.status_code})")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    # The player table is within a div with id 'LeaderBoard1_dg1_ctl'
    table = soup.find("table", id="LeaderBoard1_dg1_ctl")
    if not table:
        # FanGraphs sometimes uses id "LeaderBoard1_dg1" for the table
        table = soup.find("table", id="LeaderBoard1_dg1")
    if not table:
        # fallback: find first table in the page (not ideal)
        table = soup.find("table")
    if not table:
        print("Could not find player ratings table")
        return pd.DataFrame()

    headers = [th.get_text(strip=True).lower() for th in table.find("thead").find_all("th")]
    rows = []

    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if not cells or len(cells) != len(headers):
            continue
        row_data = {}
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            # Special handling for player name column (usually first column)
            if i == 1 or 'player' in headers[i]:  # The second column sometimes holds player name
                # Extract name from anchor tag if present
                a = cell.find("a")
                if a:
                    text = a.get_text(strip=True)
                text = clean_name(text)
            row_data[headers[i]] = text
        rows.append(row_data)

    df = pd.DataFrame(rows)

    # Select and rename relevant columns if present
    col_map = {
        'player': 'name',
        'pos': 'position',
        'rank': 'overall_rank',
        'war': 'WAR',
        'ops': 'OPS',
        'slg': 'SLG',
        'ops+': 'OPS+',
        'value': 'dynasty_value'
    }

    for old_col in list(df.columns):
        if old_col in col_map:
            df.rename(columns={old_col: col_map[old_col]}, inplace=True)

    # Convert numeric columns
    numeric_cols = ['overall_rank', 'WAR', 'OPS', 'SLG', 'OPS+', 'dynasty_value']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill NaN with zeros for numeric columns
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df.to_csv("fangraphs_hitters_rankings.csv", index=False)
    print("Saved FanGraphs hitters rankings to fangraphs_hitters_rankings.csv")

if __name__ == "__main__":
    scrape_fangraphs_hitters()
