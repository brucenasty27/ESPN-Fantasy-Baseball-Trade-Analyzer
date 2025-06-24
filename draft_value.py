from dataclasses import dataclass
from typing import List, Dict, Tuple

# Constants defining league draft settings
TEAM_COUNT = 10
ROUNDS = 16
TOTAL_PICKS = TEAM_COUNT * ROUNDS

@dataclass
class DraftPick:
    team_id: int
    round_number: int
    pick_number: int  # Overall pick number (1 to TOTAL_PICKS)

    def __str__(self) -> str:
        """
        Returns pick formatted as 'round.pick_in_round', e.g. '1.01', '16.10'.
        Zero-pads pick_in_round to 2 digits for clarity.
        """
        pick_in_round = (self.pick_number - 1) % TEAM_COUNT + 1
        return f"{self.round_number}.{pick_in_round:02d}"

def generate_draft_value_curve(
    total_picks: int = TOTAL_PICKS,
    base_value: float = 100,
    decay_rate: float = 0.975
) -> Dict[int, float]:
    """
    Generate an exponential decay curve mapping pick_number -> draft pick value.
    Higher picks have higher value, decaying by decay_rate each pick.
    """
    return {
        i + 1: round(base_value * (decay_rate ** i), 2)
        for i in range(total_picks)
    }

def generate_snake_draft_order(
    team_count: int = TEAM_COUNT,
    rounds: int = ROUNDS
) -> List[int]:
    """
    Generate the snake draft order as a list of team indices (0-based),
    alternating normal and reversed order each round.
    """
    order = []
    for rnd in range(rounds):
        if rnd % 2 == 0:
            order.extend(range(team_count))             # normal order
        else:
            order.extend(range(team_count - 1, -1, -1)) # reverse order
    return order

def assign_picks_to_teams(
    standings_teams: List[int],
    rounds: int = ROUNDS
) -> List[DraftPick]:
    """
    Assign draft picks to teams based on standings in a snake draft format.

    Args:
        standings_teams: List of team IDs ordered worst-to-best.
        rounds: Number of draft rounds.

    Returns:
        List of DraftPick objects assigned to teams with round and pick info.
    """
    team_count = len(standings_teams)
    snake_order = generate_snake_draft_order(team_count, rounds)
    picks: List[DraftPick] = []

    for pick_number, team_index in enumerate(snake_order, start=1):
        round_number = (pick_number - 1) // team_count + 1
        team_id = standings_teams[team_index]
        picks.append(DraftPick(team_id=team_id, round_number=round_number, pick_number=pick_number))

    return picks

class DraftPickValuator:
    """
    Class to assign and retrieve draft pick values based on standings and draft order.
    """

    def __init__(
        self,
        standings_team_ids: List[int],
        base_value: float = 100,
        decay_rate: float = 0.975
    ):
        # Create pick value map: overall pick number -> value
        self.pick_value_map = generate_draft_value_curve(TOTAL_PICKS, base_value, decay_rate)

        # Map (team_id, round_number) -> list of DraftPick objects (usually one pick)
        self.picks_by_team_round: Dict[Tuple[int, int], List[DraftPick]] = {}

        # Map (team_id, round_number) -> max pick value for that pick
        self.pick_lookup: Dict[Tuple[int, int], float] = {}

        # Assign picks to teams based on standings and rounds
        for pick in assign_picks_to_teams(standings_team_ids, ROUNDS):
            key = (pick.team_id, pick.round_number)
            self.picks_by_team_round.setdefault(key, []).append(pick)

        # Store max pick value per (team, round) for lookup
        for key, picks in self.picks_by_team_round.items():
            values = [self.pick_value_map.get(p.pick_number, 0) for p in picks]
            self.pick_lookup[key] = max(values, default=0)

    def get_pick_value(self, team_id: int, round_number: int) -> float:
        """
        Get the draft pick value for a given team and round.

        Args:
            team_id: The ID of the team.
            round_number: The round number (1-based).

        Returns:
            The float value of the draft pick, or 0 if not found.
        """
        return self.pick_lookup.get((team_id, round_number), 0)
