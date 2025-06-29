import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time

BASE_URL = "https://www.pitcherlist.com/category/dynasty/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0)"
}

def clean_player_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*\)", "", name)  # remove anything in parentheses
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def get_article_urls(category_url):
    """Scrape the category page to get recent article URLs."""
    resp = requests.get(category_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Articles are typically in <h2 class="entry-title"><a href="...">
    articles = soup.select("h2.entry-title a")
    urls = [a['href'] for a in articles if a.has_attr('href')]
    return urls

def scrape_rankings_from_article(article_url):
    """Extract player rankings from a single article page."""
    resp = requests.get(article_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = []
    
    # Look for tables in the article content
    tables = soup.select("article table")
    if not tables:
        # Sometimes rankings might be in lists or other formats — add custom logic if needed
        print(f"⚠️ No tables found in article {article_url}")
        return pd.DataFrame()

    for table in tables:
        try:
            df = pd.read_html(str(table))[0]
        except Exception as e:
            print(f"⚠️ Failed to parse a table in {article_url}: {e}")
            continue
        
        # Try to identify columns with player info
        # Common columns: Rank, Player, Position, Team, etc.
        # Normalize column names to lowercase
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Find likely columns
        rank_col = next((c for c in df.columns if "rank" in c), None)
        player_col = next((c for c in df.columns if "player" in c or "name" in c), None)
        pos_col = next((c for c in df.columns if "pos" in c or "position" in c), None)

        if not player_col or not rank_col:
            print(f"⚠️ Table missing rank or player column in {article_url}, skipping.")
            continue

        # Build data rows
        for _, row in df.iterrows():
            try:
                rank = int(row[rank_col])
            except:
                rank = 0
            player_name = clean_player_name(str(row[player_col]))
            position = str(row[pos_col]) if pos_col in df.columns else ""

            data.append({
                "name": player_name,
                "overall_rank": rank,
                "pos_rank": 0,
                "position": position,
                # Add placeholders for stats downstream or expand parsing as needed
                "WAR": 0,
                "ERA": 0,
                "WHIP": 0,
                "K_per_9": 0,
                "dynasty_value": 0
            })

    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def fetch_pitcherlist_dynasty_rankings():
    print("Fetching PitcherList dynasty article URLs...")
    try:
        article_urls = get_article_urls(BASE_URL)
    except Exception as e:
        print(f"❌ Failed to fetch article URLs: {e}")
        return pd.DataFrame()

    all_rankings = []
    for url in article_urls:
        print(f"Scraping rankings from article: {url}")
        try:
            df = scrape_rankings_from_article(url)
            if not df.empty:
                all_rankings.append(df)
            time.sleep(1)  # be polite
        except Exception as e:
            print(f"⚠️ Failed to scrape {url}: {e}")

    if not all_rankings:
        print("❌ No rankings data found in any articles.")
        return pd.DataFrame()

    combined_df = pd.concat(all_rankings, ignore_index=True)

    # Deduplicate by player name, keep best rank (lowest number)
    combined_df.sort_values(by="overall_rank", inplace=True)
    combined_df = combined_df.drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)

    return combined_df

if __name__ == "__main__":
    df = fetch_pitcherlist_dynasty_rankings()
    if not df.empty:
        df.to_csv("data/pitcherlist_dynasty_rankings.csv", index=False)
        print(f"✅ Saved PitcherList dynasty rankings for {len(df)} players to data/pitcherlist_dynasty_rankings.csv")
    else:
        print("❌ No PitcherList dynasty rankings scraped.")
