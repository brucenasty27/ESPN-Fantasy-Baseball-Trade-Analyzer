import pandas as pd
import re

# Load dynasty rankings once on module load
rankings_df = pd.read_csv("dynasty_rankings.csv")
rankings_df["name_clean"] = rankings_df["name"].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)

def normalize_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower())

def get_player_rank(name: str):
    name_clean = normalize_name(name)
    match = rankings_df[rankings_df["name_clean"] == name_clean]
    if not match.empty:
        return match.iloc[0]
    return None

def get_dynasty_value(player, age: int = None, recent_score: float = None) -> float:
    """
    Calculate a player's dynasty value.

    Args:
        player: ESPN player object with attributes or a string player name.
        age: Optional player age override.
        recent_score: Optional recent performance score override.

    Returns:
        float: Dynasty value score.
    """
    # Handle ESPN player object
    if hasattr(player, 'name'):
        name = player.name
        age = getattr(getattr(player, 'player', None), 'age', age or 25)
        stats = getattr(player, 'stats', {}).get('2025') or getattr(player, 'stats', {}).get('2024')
        recent_score = stats.get('points', 0) if stats else (recent_score or 0)
        is_prospect = "Minors" in getattr(player, 'injuryStatus', "") or getattr(player, 'is_injured_reserve', False)
        prospect_bonus = 10 if is_prospect else 0
    else:
        # Raw string fallback
        name = player
        age = age or 25
        recent_score = recent_score or 0
        prospect_bonus = 0

    ranking = get_player_rank(name)
    if ranking is None:
        return 0  # Player not ranked

    # Scoring logic
    rank_score = max(0, 300 - ranking["overall_rank"])
    pos_score = max(0, 100 - ranking["pos_rank"])
    age_score = max(0, (30 - age)) * 0.5
    perf_score = recent_score * 0.5

    return round(rank_score + pos_score + age_score + perf_score + prospect_bonus, 2)
