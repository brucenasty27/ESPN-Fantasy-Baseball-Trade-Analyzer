import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

URL = "https://www.fangraphs.com/fantasy-tools/player-rater?leaguetype=1&pos=&posType=pit"

def clean_name(name):
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_fangraphs_pitchers():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {URL} (status {response.status_code})")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", id="LeaderBoard1_dg1_ctl") or \
            soup.find("table", id="LeaderBoard1_dg1") or \
            soup.find("table")

    if not table:
        print("Could not find player ratings table")
        return pd.DataFrame()

    thead = table.find("thead")
    if thead:
        headers_row = [th.get_text(strip=True).lower() for th in thead.find_all("th")]
    else:
        first_tr = table.find("tr")
        if not first_tr:
            print("No header row found in table")
            return pd.DataFrame()
        headers_row = [th.get_text(strip=True).lower() for th in first_tr.find_all(["th", "td"])]

    rows = []
    tbody = table.find("tbody")
    if not tbody:
        print("No tbody found in table")
        return pd.DataFrame()

    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if not cells or len(cells) != len(headers_row):
            continue
        row_data = {}
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            if i == 1 or 'player' in headers_row[i]:
                a = cell.find("a")
                if a:
                    text = a.get_text(strip=True)
                text = clean_name(text)
            row_data[headers_row[i]] = text
        rows.append(row_data)

    df = pd.DataFrame(rows)

    col_map = {
        'player': 'name',
        'pos': 'position',
        'rank': 'overall_rank',
        'w': 'W',
        'sv': 'SV',
        'k': 'K',
        'era': 'ERA',
        'whip': 'WHIP',
        'ip': 'IP'
    }

    df_cols_lower = {col.lower(): col for col in df.columns}
    for key, new_col in col_map.items():
        if key in df_cols_lower and new_col not in df.columns:
            old_col = df_cols_lower[key]
            df.rename(columns={old_col: new_col}, inplace=True)

    for col in ['overall_rank', 'pos_rank', 'position', 'W', 'SV', 'K', 'ERA', 'WHIP', 'IP']:
        if col not in df.columns:
            df[col] = 0 if col != 'position' else ''

    numeric_cols = ['overall_rank', 'pos_rank', 'W', 'SV', 'K', 'ERA', 'WHIP', 'IP']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df[['name', 'overall_rank', 'pos_rank', 'position', 'W', 'SV', 'K', 'ERA', 'WHIP', 'IP']]

if __name__ == "__main__":
    df = fetch_fangraphs_pitchers()
    print(f"Fetched {len(df)} pitchers from FanGraphs")
    df.to_csv("data/fangraphs_pitchers.csv", index=False)
