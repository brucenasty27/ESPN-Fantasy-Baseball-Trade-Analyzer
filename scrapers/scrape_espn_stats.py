from espn_api.baseball import League
import pandas as pd

def clean_name(name: str) -> str:
    """Normalize player names for consistent matching."""
    if not isinstance(name, str):
        return ""
    # Lowercase and strip whitespace
    return name.lower().strip()

def fetch_espn_hitter_stats(league: League) -> pd.DataFrame:
    """Fetch hitter stats from ESPN league roster."""
    hitters = []
    for team in league.teams:
        for player in team.roster:
            pos = player.position
            # Filter out pitchers
            if pos in ["SP", "RP", "P"]:
                continue
            stats = player.stats or {}
            hitters.append({
                "name": clean_name(player.name),
                "position": pos,
                "HR": stats.get("HR", 0),
                "R": stats.get("R", 0),
                "RBI": stats.get("RBI", 0),
                "SB": stats.get("SB", 0),
                "AVG": stats.get("AVG", 0.0),
                "BB": stats.get("BB", 0),
            })
    return pd.DataFrame(hitters)

def fetch_espn_pitcher_stats(league: League) -> pd.DataFrame:
    """Fetch pitcher stats from ESPN league roster."""
    pitchers = []
    for team in league.teams:
        for player in team.roster:
            pos = player.position
            # Keep only pitchers
            if pos not in ["SP", "RP", "P"]:
                continue
            stats = player.stats or {}
            pitchers.append({
                "name": clean_name(player.name),
                "position": pos,
                "W": stats.get("W", 0),
                "SV": stats.get("SV", 0),
                "K": stats.get("K", 0),
                "ERA": stats.get("ERA", 0.0),
                "WHIP": stats.get("WHIP", 0.0),
                "IP": stats.get("IP", 0.0),  # Innings pitched, might be needed for weighting
            })
    return pd.DataFrame(pitchers)

if __name__ == "__main__":
    # Example usage - replace LEAGUE_ID and YEAR accordingly
    # from espn_api.baseball import League
    # league = League(league_id=LEAGUE_ID, year=YEAR)
    # hitters_df = fetch_espn_hitter_stats(league)
    # pitchers_df = fetch_espn_pitcher_stats(league)
    # print(hitters_df.head())
    # print(pitchers_df.head())
    pass
