import os
import pandas as pd
from dotenv import load_dotenv
from espn_api.baseball import League
from rankings import fetch_all_sources

def load_espn_league():
    load_dotenv()

    try:
        league_id = int(os.getenv("LEAGUE_ID"))
        year = int(os.getenv("YEAR"))
        espn_s2 = os.getenv("ESPN_S2")
        swid = os.getenv("SWID")

        if not all([league_id, year, espn_s2, swid]):
            raise ValueError("Missing one or more required ESPN credentials in .env")

        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
        return league
    except Exception as e:
        print(f"❌ Error loading ESPN league: {e}")
        return None

def update_rankings():
    print("📊 Updating dynasty rankings...")

    league = load_espn_league()
    if league is None:
        print("⚠️ Failed to initialize ESPN League. Aborting rankings update.")
        return

    df = fetch_all_sources(league)

    if df.empty:
        print("⚠️ No data fetched. Rankings update aborted.")
        return

    if "name" not in df.columns:
        print("❌ 'name' column not found in dataframe. Check scraper output.")
        return

    df["name"] = df["name"].astype(str).str.strip().str.lower()
    df["position"] = df["position"].astype(str).str.upper()

    print(f"✅ Rankings updated with {len(df)} players.")
    print(df[["name", "dynasty_value", "position"]].head(10))

if __name__ == "__main__":
    update_rankings()
