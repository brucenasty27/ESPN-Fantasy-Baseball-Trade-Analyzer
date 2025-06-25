import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.rotowire.com/baseball/rankings.php?pos=ALL"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0)"
}

def clean_player_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_rotowire_rankings():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.find("table")
        if not table:
            raise RuntimeError("Rotowire rankings table not found")

        rows = table.find_all("tr")[1:]  # skip header
        data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            try:
                rank = int(cells[0].text.strip())
            except ValueError:
                continue  # Skip invalid ranks

            player_name = clean_player_name(cells[1].text.strip())
            position = cells[2].text.strip()

            data.append({
                "name": player_name,
                "overall_rank": rank,
                "pos_rank": 0,  # Placeholder for positional rank
                "position": position
            })

        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch Rotowire rankings: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_rotowire_rankings()
    if not df.empty:
        print(f"✅ Fetched {len(df)} players from Rotowire")
        df.to_csv("rotowire_rankings.csv", index=False)
    else:
        print("❌ No data fetched from Rotowire.")
