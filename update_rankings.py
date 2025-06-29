import os
from dotenv import load_dotenv
from espn_api.baseball import League
from rankings import fetch_all_sources, combine_rankings

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
    print("📊 Starting dynasty rankings update...")

    league = load_espn_league()
    if league is None:
        print("⚠️ Failed to initialize ESPN League. Aborting rankings update.")
        return

    try:
        dfs = fetch_all_sources(league)
        combined_df = combine_rankings(dfs)

        if combined_df.empty:
            print("⚠️ Combined rankings data is empty. Update aborted.")
            return

        output_path = os.path.join("data", "dynasty_rankings_cleaned.csv")
        combined_df.to_csv(output_path, index=False)
        print(f"✅ Dynasty rankings successfully updated and saved to {output_path}")
    except Exception as e:
        print(f"❌ Error during rankings update: {e}")

if __name__ == "__main__":
    update_rankings()
