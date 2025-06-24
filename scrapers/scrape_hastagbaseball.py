import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

URL = "https://hashtagbaseball.com/fantasy-baseball-rankings"

def clean_name(name):
    # Remove suffixes and excess whitespace
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def scrape_hashtagbaseball():
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Failed to fetch {URL} (status {response.status_code})")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find tables for Hitters and Pitchers
    # The site structure can change, so inspect to confirm selectors if issues occur

    tables = soup.find_all("table")

    if not tables or len(tables) < 2:
        print("Could not find expected tables for Hitters and Pitchers")
        return pd.DataFrame()

    # Hashtag Baseball has two main tables: hitters first, pitchers second
    hitters_table = tables[0]
    pitchers_table = tables[1]

    def parse_table(table, position_group):
        rows = []
        headers = [th.get_text(strip=True).lower() for th in table.find_all("thead")[0].find_all("th")]

        for tr in table.find("tbody").find_all("tr"):
            cells = tr.find_all("td")
            if not cells or len(cells) != len(headers):
                continue

            data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
            data['position_group'] = position_group
            rows.append(data)

        return pd.DataFrame(rows)

    hitters_df = parse_table(hitters_table, "hitters")
    pitchers_df = parse_table(pitchers_table, "pitchers")

    # Combine and clean
    df = pd.concat([hitters_df, pitchers_df], ignore_index=True)

    # Standardize column names
    rename_map = {
        'player': 'name',
        'pos': 'position',
        'ovr': 'overall_rank',
        'dynasty value': 'dynasty_value',
        'war': 'WAR',
        'ops': 'OPS',
        'slg': 'SLG',
        'ops+': 'OPS+'
    }

    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Clean player names
    if 'name' in df.columns:
        df['name'] = df['name'].apply(clean_name)
    else:
        print("Warning: 'name' column not found")

    # Convert numeric columns
    for col in ['overall_rank', 'dynasty_value', 'WAR', 'OPS', 'SLG', 'OPS+']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill NaNs with zeros for numeric columns
    for col in ['overall_rank', 'dynasty_value', 'WAR', 'OPS', 'SLG', 'OPS+']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Filter out rows missing a player name or position
    df.dropna(subset=['name', 'position'], inplace=True)

    # Save to CSV
    df.to_csv("hashtagbaseball_rankings.csv", index=False)
    print(f"Saved Hashtag Baseball rankings to hashtagbaseball_rankings.csv")

if __name__ == "__main__":
    scrape_hashtagbaseball()
