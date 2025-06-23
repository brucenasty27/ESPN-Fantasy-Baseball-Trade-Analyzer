# draft_value.py

import numpy as np
from dataclasses import dataclass

@dataclass
class DraftPick:
    team_id: int
    round_number: int
    pick_number: int  # overall pick number from 1 to 160

    def __str__(self):
        pick_str = f"{(self.pick_number - 1) % 10 + 1:02d}"
        return f"{self.round_number}.{pick_str}"


# Create draft value curve (exponential decay or similar realistic model)
def generate_draft_value_curve(total_picks=160, base_value=100, decay_rate=0.975):
    return {i + 1: round(base_value * (decay_rate ** i), 2) for i in range(total_picks)}


# Snake draft logic to determine draft slot from standings
def generate_snake_draft_order(team_count=10, rounds=16):
    order = []
    for rnd in range(rounds):
        if rnd % 2 == 0:
            order.extend(list(range(team_count)))  # 0 to 9
        else:
            order.extend(list(range(team_count - 1, -1, -1)))  # 9 to 0
    return order  # length 160


def assign_picks_to_teams(standings_teams, rounds=16):
    """
    standings_teams: List of team IDs in reverse order of finish (worst first, best last)
    """
    team_count = len(standings_teams)
    snake_order = generate_snake_draft_order(team_count, rounds)
    pick_map = []
    for pick_number, team_idx in enumerate(snake_order, start=1):
        round_number = (pick_number - 1) // team_count + 1
        team_id = standings_teams[team_idx]
        pick = DraftPick(team_id=team_id, round_number=round_number, pick_number=pick_number)
        pick_map.append(pick)
    return pick_map  # list of DraftPick


# Utility to lookup pick value
class DraftPickValuator:
    def __init__(self, standings_team_ids):
        self.pick_value_map = generate_draft_value_curve()
        self.picks_by_team = {}
        for pick in assign_picks_to_teams(standings_team_ids):
            self.picks_by_team.setdefault((pick.team_id, pick.round_number), []).append(pick)
        self.pick_lookup = {
            (pick.team_id, pick.round_number): max(
                [self.pick_value_map.get(p.pick_number, 0) for p in picks], default=0
            )
            for (pick.team_id, pick.round_number), picks in self.picks_by_team.items()
        }

    def get_pick_value(self, team_id: int, round_number: int) -> float:
        return self.pick_lookup.get((team_id, round_number), 0)
