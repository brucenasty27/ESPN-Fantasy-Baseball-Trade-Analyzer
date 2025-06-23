from dataclasses import dataclass

# Constants
TEAM_COUNT = 10
ROUNDS = 16
TOTAL_PICKS = TEAM_COUNT * ROUNDS

@dataclass
class DraftPick:
    team_id: int
    round_number: int
    pick_number: int  # Overall pick number (1 to TOTAL_PICKS)

    def __str__(self):
        pick_str = f"{(self.pick_number - 1) % TEAM_COUNT + 1:02d}"
        return f"{self.round_number}.{pick_str}"


def generate_draft_value_curve(total_picks=TOTAL_PICKS, base_value=100, decay_rate=0.975):
    """
    Exponential draft pick value decay curve.
    Returns a dict mapping pick_number -> value.
    """
    return {
        i + 1: round(base_value * (decay_rate ** i), 2)
        for i in range(total_picks)
    }


def generate_snake_draft_order(team_count=TEAM_COUNT, rounds=ROUNDS):
    """
    Generate full pick sequence in snake format.
    """
    order = []
    for rnd in range(rounds):
        if rnd % 2 == 0:
            order.extend(list(range(team_count)))  # Normal order
        else:
            order.extend(list(range(team_count - 1, -1, -1)))  # Reverse order
    return order


def assign_picks_to_teams(standings_teams, rounds=ROUNDS):
    """
    Assign picks to team_ids using a snake draft based on standings.

    :param standings_teams: List of team IDs (worst to best).
    :return: List of DraftPick instances with team/round/pick data.
    """
    team_count = len(standings_teams)
    snake_order = generate_snake_draft_order(team_count, rounds)
    pick_map = []

    for pick_number, team_index in enumerate(snake_order, start=1):
        round_number = (pick_number - 1) // team_count + 1
        team_id = standings_teams[team_index]
        pick_map.append(DraftPick(team_id=team_id, round_number=round_number, pick_number=pick_number))

    return pick_map


class DraftPickValuator:
    def __init__(self, standings_team_ids, base_value=100, decay_rate=0.975):
        self.pick_value_map = generate_draft_value_curve(TOTAL_PICKS, base_value, decay_rate)
        self.picks_by_team_round = {}  # (team_id, round) -> list of DraftPick
        self.pick_lookup = {}          # (team_id, round) -> value

        for pick in assign_picks_to_teams(standings_team_ids, ROUNDS):
            key = (pick.team_id, pick.round_number)
            self.picks_by_team_round.setdefault(key, []).append(pick)

        for key, picks in self.picks_by_team_round.items():
            values = [self.pick_value_map.get(p.pick_number, 0) for p in picks]
            self.pick_lookup[key] = max(values, default=0)

    def get_pick_value(self, team_id: int, round_number: int) -> float:
        return self.pick_lookup.get((team_id, round_number), 0)
