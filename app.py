import streamlit as st
from espn_api.baseball import League
from player_value import get_dynasty_value
import datetime
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 🔐 Load environment variables from .env file
load_dotenv()

# ESPN credentials (hidden securely in .env)
LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
SEASON_YEAR = int(os.getenv("SEASON_YEAR"))
SWID = os.getenv("SWID")
ESPN_S2 = os.getenv("ESPN_S2")

st.title("🏆 Dynasty Trade Analyzer with Draft Picks")

@dataclass
class DraftPick:
    round_number: int
    year: int

    def __str__(self):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(
            self.round_number if self.round_number < 20 else 0, "th"
        )
        return f"{self.year} {self.round_number}{suffix} Round Pick"

DRAFT_ROUNDS = 16
NEXT_DRAFT_YEAR = SEASON_YEAR + 1

def generate_team_picks(team_name):
    return [DraftPick(round_number=i, year=NEXT_DRAFT_YEAR) for i in range(1, DRAFT_ROUNDS + 1)]

DRAFT_PICK_VALUES = {
    1: 100, 2: 80, 3: 65, 4: 50, 5: 40,
    6: 32, 7: 25, 8: 20, 9: 16, 10: 13,
    11: 11, 12: 9, 13: 7, 14: 5, 15: 3, 16: 1,
}

def get_draft_pick_value(pick: DraftPick):
    return DRAFT_PICK_VALUES.get(pick.round_number, 0)

@st.cache_resource(show_spinner=False)
def load_league():
    return League(
        league_id=LEAGUE_ID,
        year=SEASON_YEAR,
        swid=SWID,
        espn_s2=ESPN_S2
    )

if "last_sync" not in st.session_state:
    st.session_state.last_sync = None

if st.button("🔄 Sync League Data Now"):
    with st.spinner("Syncing league data..."):
        st.cache_resource.clear()
        league = load_league()
        st.session_state.last_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.success(f"✅ League data synced at {st.session_state.last_sync}")
else:
    league = load_league()

if st.session_state.last_sync:
    st.caption(f"Last synced: {st.session_state.last_sync}")

team_names = [team.team_name for team in league.teams]
team_1_name = st.selectbox("Select Team 1", team_names, index=0)
team_2_name = st.selectbox("Select Team 2", team_names, index=1)

team_1 = next(t for t in league.teams if t.team_name == team_1_name)
team_2 = next(t for t in league.teams if t.team_name == team_2_name)

team_1_roster = {p.name: p for p in team_1.roster}
team_2_roster = {p.name: p for p in team_2.roster}

trade_from_team_1 = st.multiselect("Team 1 Trades Away (Players)", list(team_1_roster.keys()))
trade_from_team_2 = st.multiselect("Team 2 Trades Away (Players)", list(team_2_roster.keys()))

team_1_picks = generate_team_picks(team_1_name)
team_2_picks = generate_team_picks(team_2_name)

trade_picks_team_1 = st.multiselect(
    "Team 1 Trades Away (Draft Picks)",
    options=team_1_picks,
    format_func=str
)

trade_picks_team_2 = st.multiselect(
    "Team 2 Trades Away (Draft Picks)",
    options=team_2_picks,
    format_func=str
)

def calculate_trade_value(players, picks):
    player_value = sum(get_dynasty_value(p) for p in players)
    picks_value = sum(get_draft_pick_value(p) for p in picks)
    return player_value + picks_value

if trade_from_team_1 or trade_from_team_2 or trade_picks_team_1 or trade_picks_team_2:
    team_1_players = [team_1_roster[name] for name in trade_from_team_1]
    team_2_players = [team_2_roster[name] for name in trade_from_team_2]

    team_1_value = calculate_trade_value(team_1_players, trade_picks_team_1)
    team_2_value = calculate_trade_value(team_2_players, trade_picks_team_2)

    st.markdown("### 📊 Trade Value Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Team 1 Total Value", team_1_value)
    with col2:
        st.metric("Team 2 Total Value", team_2_value)

    delta = round(team_1_value - team_2_value, 2)
    if abs(delta) < 5:
        st.success("✅ This trade looks relatively balanced.")
    elif delta > 5:
        st.warning(f"⚠️ Team 1 appears to win this trade by {delta} points.")
    else:
        st.warning(f"⚠️ Team 2 appears to win this trade by {abs(delta)} points.")

    def generate_trade_explanation(players_1, picks_1, players_2, picks_2, value_1, value_2):
        delta = round(value_1 - value_2, 2)
        verdict = (
            "This trade is fairly even overall." if abs(delta) < 5 else
            f"Team 1 has a noticeable edge in value by {delta} points." if delta > 5 else
            f"Team 2 has a noticeable edge in value by {abs(delta)} points."
        )

        lines = []
        for p in players_1:
            lines.append(f"- {p.name} (Team 1): {get_dynasty_value(p)} pts")
        for dp in picks_1:
            lines.append(f"- {str(dp)} (Team 1 Draft Pick): {get_draft_pick_value(dp)} pts")
        for p in players_2:
            lines.append(f"- {p.name} (Team 2): {get_dynasty_value(p)} pts")
        for dp in picks_2:
            lines.append(f"- {str(dp)} (Team 2 Draft Pick): {get_draft_pick_value(dp)} pts")

        return f"""**🧠 Trade Insight**  
{verdict}  
**Player & Pick Breakdown:**  
{chr(10).join(lines)}"""

    st.markdown("---")
    st.markdown(generate_trade_explanation(team_1_players, trade_picks_team_1, team_2_players, trade_picks_team_2, team_1_value, team_2_value))

    def who_says_no(team_1_players, team_2_players, picks_1, picks_2, team_1_value, team_2_value):
        delta = round(team_1_value - team_2_value, 2)
        big_gap = 15
        top_player_threshold = 50

        for p in team_1_players:
            val = get_dynasty_value(p)
            if val > top_player_threshold and delta < -big_gap:
                return f"🚫 Team 1 likely says NO: losing top player {p.name} with insufficient return."
        for p in team_2_players:
            val = get_dynasty_value(p)
            if val > top_player_threshold and delta > big_gap:
                return f"🚫 Team 2 likely says NO: losing top player {p.name} with insufficient return."

        for dp in picks_1:
            val = get_draft_pick_value(dp)
            if val > top_player_threshold and delta < -big_gap:
                return f"🚫 Team 1 likely says NO: losing valuable draft pick {str(dp)} with insufficient return."
        for dp in picks_2:
            val = get_draft_pick_value(dp)
            if val > top_player_threshold and delta > big_gap:
                return f"🚫 Team 2 likely says NO: losing valuable draft pick {str(dp)} with insufficient return."

        if delta > big_gap:
            return "🚫 Team 2 likely says NO: trade heavily favors Team 1."
        if delta < -big_gap:
            return "🚫 Team 1 likely says NO: trade heavily favors Team 2."

        return "✅ Both teams are likely to accept this trade."

    st.markdown("---")
    st.markdown("### 🤖 Trade Negotiation Simulation")
    response = who_says_no(team_1_players, team_2_players, trade_picks_team_1, trade_picks_team_2, team_1_value, team_2_value)
    st.info(response)
