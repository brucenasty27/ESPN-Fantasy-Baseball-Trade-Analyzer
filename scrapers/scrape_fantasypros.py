import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

HITTERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"
PITCHERS_URL = "https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def scrape_fantasypros_table(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"id": "data"})
    if not table:
        raise ValueError("Could not find rankings table on FantasyPros")

    df = pd.read_html(str(table))[0]
    return df

def clean_and_merge():
    print("Scraping FantasyPros dynasty hitters...")
    hitters_df = scrape_fantasypros_table(HITTERS_URL)
    hitters_df["position"] = "H"

    time.sleep(1)

    print("Scraping FantasyPros dynasty pitchers...")
    pitchers_df = scrape_fantasypros_table(PITCHERS_URL)
    pitchers_df["position"] = "P"

    combined = pd.concat([hitters_df, pitchers_df], ignore_index=True)

    # Clean names
    combined.rename(columns={"Player Name": "name", "Rank": "overall_rank"}, inplace=True)
    combined = combined[["name", "overall_rank", "position"]]

    # Lowercase clean names
    combined["name"] = combined["name"].str.strip().str.lower()
    combined["overall_rank"] = pd.to_numeric(combined["overall_rank"], errors="coerce")

    combined.dropna(subset=["name", "overall_rank"], inplace=True)

    print(f"Saving {len(combined)} FantasyPros dynasty player rankings...")
    combined.to_csv("fantasypros_rankings.csv", index=False)

if __name__ == "__main__":
    clean_and_merge()
