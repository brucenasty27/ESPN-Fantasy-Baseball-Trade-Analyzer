import os
import pandas as pd
from dotenv import load_dotenv
from espn_api.baseball import League
from rankings import (
    fetch_all_sources,
    combine_rankings,
    clean_player_name,
    calculate_dynasty_value_hitter,
    calculate_dynasty_value_pitcher,
)

load_dotenv()

def create_espn_league():
    return League(
        league_id=int(os.getenv("LEAGUE_ID")),
        year=int(os.getenv("SEASON_YEAR")),
        swid=os.getenv("SWID"),
        espn_s2=os.getenv("ESPN_S2")
    )

def fetch_espn_stats(league):
    data = []
    for team in league.teams:
        for player in team.roster:
            stats = player.stats or {}
            name = clean_player_name(player.name)
            position = player.position or ""

            record = {
                "name": name,
                "position": position,
                "HR": stats.get("HR", 0),
                "R": stats.get("R", 0),
                "RBI": stats.get("RBI", 0),
                "SB": stats.get("SB", 0),
                "BB": stats.get("BB", 0),
                "AVG": stats.get("AVG", 0.0),
                "W": stats.get("W", 0),
                "SV": stats.get("SV", 0),
                "K": stats.get("K", 0),
                "ERA": stats.get("ERA", 0.0),
                "WHIP": stats.get("WHIP", 0.0),
                "IP": stats.get("IP", 0.0),
                "overall_rank": 0,
                "pos_rank": 0,
            }
            data.append(record)
    return pd.DataFrame(data)

def main():
    print("🔄 Updating dynasty rankings with ESPN league context...")

    league = create_espn_league()
    espn_df = fetch_espn_stats(league)
    other_sources = fetch_all_sources()

    all_dataframes = other_sources + [espn_df]
    final_df = combine_rankings(all_dataframes)

    output_path = os.path.join("data", "dynasty_rankings_cleaned.csv")
    final_df.to_csv(output_path, index=False)

    print(f"✅ Dynasty rankings (with ESPN league data) saved to: {output_path}")

if __name__ == "__main__":
    main()
