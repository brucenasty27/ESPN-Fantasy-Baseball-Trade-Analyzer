# player_value.py

import pandas as pd
import numpy as np
import re

# ---------------------------
# Dynasty Player Valuation
# ---------------------------

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
    if hasattr(player, 'name'):
        name = player.name
        age = getattr(getattr(player, 'player', None), 'age', age or 25)
        stats = getattr(player, 'stats', {}).get('2025') or getattr(player, 'stats', {}).get('2024')
        recent_score = stats.get('points', 0) if stats else (recent_score or 0)
        is_prospect = "Minors" in getattr(player, 'injuryStatus', "") or getattr(player, 'is_injured_reserve', False)
        prospect_bonus = 10 if is_prospect else 0
    else:
        name = player
        age = age or 25
        recent_score = recent_score or 0
        prospect_bonus = 0

    ranking = get_player_rank(name)
    if ranking is None:
        return 0

    rank_score = max(0, 300 - ranking["overall_rank"])
    pos_score = max(0, 100 - ranking["pos_rank"])
    age_score = max(0, (30 - age)) * 0.5
    perf_score = recent_score * 0.5

    return round(rank_score + pos_score + age_score + perf_score + prospect_bonus, 2)

# ---------------------------
# Draft Pick Valuation - Simple Mode
# ---------------------------

TOTAL_PICKS = 160
PICKS_PER_ROUND = 10
TOTAL_ROUNDS = 16

def generate_value_curve():
    values = []
    for pick in range(1, TOTAL_PICKS + 1):
        value = round(300 * (pick ** -0.35), 2)
        values.append(value)
    return values

DRAFT_PICK_VALUE_LIST = generate_value_curve()

ROUND_PICK_VALUES = {
    round_num: round(np.mean(
        DRAFT_PICK_VALUE_LIST[(round_num - 1) * PICKS_PER_ROUND: round_num * PICKS_PER_ROUND]
    ), 2)
    for round_num in range(1, TOTAL_ROUNDS + 1)
}

def get_simple_draft_pick_value(pick):
    return ROUND_PICK_VALUES.get(pick.round_number, 0)
