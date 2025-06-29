from espn_api.baseball import League
import pandas as pd

def clean_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.lower().strip()

def fetch_espn_hitter_stats(league: League) -> pd.DataFrame:
    hitters = []
    for team in league.teams:
        for player in team.roster:
            if player.position in ["SP", "RP", "P"]:
                continue
            stats = player.stats or {}
            hitters.append({
                "name": clean_name(player.name),
                "position": player.position,
                "HR": stats.get("HR", 0),
                "R": stats.get("R", 0),
                "RBI": stats.get("RBI", 0),
                "SB": stats.get("SB", 0),
                "AVG": stats.get("AVG", 0.0),
                "BB": stats.get("BB", 0),
            })
    return pd.DataFrame(hitters)

def fetch_espn_pitcher_stats(league: League) -> pd.DataFrame:
    pitchers = []
    for team in league.teams:
        for player in team.roster:
            if player.position not in ["SP", "RP", "P"]:
                continue
            stats = player.stats or {}
            pitchers.append({
                "name": clean_name(player.name),
                "position": player.position,
                "W": stats.get("W", 0),
                "SV": stats.get("SV", 0),
                "K": stats.get("K", 0),
                "ERA": stats.get("ERA", 0.0),
                "WHIP": stats.get("WHIP", 0.0),
                "IP": stats.get("IP", 0.0),
            })
    return pd.DataFrame(pitchers)
