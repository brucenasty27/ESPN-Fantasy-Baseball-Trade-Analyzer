import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.mlb.com/prospects/top100"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0)"
}

def clean_player_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_mlbpipeline_prospects():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the prospects table, may need to confirm selector on site
        table = soup.find("table")
        if not table:
            raise RuntimeError("MLB Pipeline prospects table not found")

        rows = table.find_all("tr")[1:]  # skip header row
        data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            try:
                rank = int(cells[0].text.strip())
            except:
                rank = 0
            player_name = clean_player_name(cells[1].text.strip())
            position = cells[2].text.strip()

            data.append({
                "name": player_name,
                "overall_rank": rank,
                "pos_rank": 0,
                "position": position,
                # Prospects usually have limited stats, so leave them blank or zero
                "WAR": 0,
                "OPS": 0,
                "SLG": 0,
                "OPS+": 0,
                "dynasty_value": 0
            })

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"Warning: Failed to fetch MLB Pipeline prospects: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_mlbpipeline_prospects()
    if not df.empty:
        df.to_csv("mlbpipeline_prospects.csv", index=False)
        print(f"✅ Saved MLB Pipeline prospects ({len(df)}) to mlbpipeline_prospects.csv")
    else:
        print("❌ No data fetched from MLB Pipeline")
