import streamlit as st
from espn_api.baseball import League
from player_value import get_dynasty_value, get_simple_draft_pick_value
from draft_value import DraftPickValuator, DraftPick
import datetime
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import subprocess

# Load environment variables from .env file
load_dotenv()

# Environment variables validation
try:
    LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
    SEASON_YEAR = int(os.getenv("SEASON_YEAR"))
    SWID = os.getenv("SWID")
    ESPN_S2 = os.getenv("ESPN_S2")
    if not (SWID and ESPN_S2):
        raise ValueError("Missing SWID or ESPN_S2 tokens")
except Exception as e:
    st.error(f"Error loading environment variables: {e}")
    st.stop()

st.set_page_config(page_title="Dynasty Trade Analyzer", layout="wide")
st.title("🏆 Dynasty Trade Analyzer with Draft Picks")

@dataclass
class DraftPickSimple:
    round_number: int
    year: int

    def __str__(self):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(
            self.round_number if self.round_number < 20 else 0, "th"
        )
        return f"{self.year} {self.round_number}{suffix} Round Pick"

DRAFT_ROUNDS = 16
NEXT_DRAFT_YEAR = SEASON_YEAR + 1

def generate_team_picks():
    return [DraftPickSimple(round_number=i, year=NEXT_DRAFT_YEAR) for i in range(1, DRAFT_ROUNDS + 1)]

@st.cache_resource(show_spinner=False)
def load_league():
    try:
        league = League(
            league_id=LEAGUE_ID,
            year=SEASON_YEAR,
            swid=SWID,
            espn_s2=ESPN_S2
        )
        return league
    except Exception as e:
        st.error(f"Failed to load league: {e}")
        st.stop()

def get_team_logo(team):
    if hasattr(team, "team_id") and team.team_id:
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team.team_id}.png"
    return ""

def calculate_trade_value(players, picks, pick_valuator=None, mode="simple", team_id=None):
    player_value = sum(get_dynasty_value(p) for p in players)
    if mode == "advanced" and pick_valuator and team_id is not None:
        picks_value = sum(pick_valuator.get_pick_value(team_id, p.round_number) for p in picks)
    else:
        picks_value = sum(get_simple_draft_pick_value(p) for p in picks)
    return player_value + picks_value

def refresh_rankings():
    try:
        result = subprocess.run(["python", "update_rankings.py"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error refreshing rankings: {e.stderr}"

# Session state defaults
if "trade_from_team_1" not in st.session_state:
    st.session_state.trade_from_team_1 = []
if "trade_from_team_2" not in st.session_state:
    st.session_state.trade_from_team_2 = []
if "trade_picks_team_1_rounds" not in st.session_state:
    st.session_state.trade_picks_team_1_rounds = []
if "trade_picks_team_2_rounds" not in st.session_state:
    st.session_state.trade_picks_team_2_rounds = []
if "pick_value_mode" not in st.session_state:
    st.session_state.pick_value_mode = "simple"
if "last_sync" not in st.session_state:
    st.session_state.last_sync = None

# Sidebar UI
with st.sidebar:
    st.header("Settings")
    if st.button("🔄 Refresh Dynasty Rankings Now"):
        with st.spinner("Refreshing dynasty rankings..."):
            output = refresh_rankings()
            st.success("Dynasty rankings refreshed.")
            st.text(output)

    st.markdown("---")
    mode = st.selectbox(
        "Draft Pick Valuation Mode",
        options=["simple", "advanced"],
        index=0 if st.session_state.pick_value_mode == "simple" else 1,
        help="Simple: average round values. Advanced: team- and pick-specific values based on standings."
    )
    st.session_state.pick_value_mode = mode

    if st.button("🔄 Sync League Data Now"):
        with st.spinner("Syncing league data..."):
            st.cache_resource.clear()
            league = load_league()
            st.session_state.last_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"✅ League data synced at {st.session_state.last_sync}")

# Load league on start or reload
if "league" not in st.session_state or st.session_state.get("last_sync") is None:
    league = load_league()
    st.session_state.league = league
else:
    league = st.session_state.league

if st.session_state.last_sync:
    st.caption(f"Last synced: {st.session_state.last_sync}")

team_names = [team.team_name for team in league.teams]

# Prepare DraftPickValuator if advanced mode enabled
pick_valuator = None
if st.session_state.pick_value_mode == "advanced":
    # Worst to best team_ids based on wins (lowest first)
    standings_team_ids = [team.team_id for team in sorted(league.teams, key=lambda t: t.wins)]
    pick_valuator = DraftPickValuator(standings_team_ids)

tab_trade, tab_search = st.tabs(["Trade Analyzer", "Player Search"])

with tab_trade:
    st.header("🤝 Trade Analyzer")

    col1, col2 = st.columns([3, 3])
    with col1:
        selected_team_1 = st.selectbox("Select Team 1", team_names, index=0)
    with col2:
        selected_team_2 = st.selectbox("Select Team 2", team_names, index=1)

    team_1 = next(t for t in league.teams if t.team_name == selected_team_1)
    team_2 = next(t for t in league.teams if t.team_name == selected_team_2)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(get_team_logo(team_1), width=75)
        st.markdown(f"### {selected_team_1}")
    with col2:
        st.image(get_team_logo(team_2), width=75)
        st.markdown(f"### {selected_team_2}")

    team_1_roster = {p.name: p for p in team_1.roster}
    team_2_roster = {p.name: p for p in team_2.roster}

    team_1_picks = generate_team_picks()
    team_2_picks = generate_team_picks()

    trade_from_team_1 = st.multiselect(
        "Players from Team 1",
        list(team_1_roster.keys()),
        default=st.session_state.trade_from_team_1,
        help="Select players Team 1 is trading away"
    )
    st.session_state.trade_from_team_1 = trade_from_team_1

    trade_picks_team_1_rounds = st.multiselect(
        "Draft Pick Rounds from Team 1",
        options=list(range(1, DRAFT_ROUNDS + 1)),
        format_func=lambda r: f"{NEXT_DRAFT_YEAR} {r}{'th' if r>3 else ['st','nd','rd'][r-1]} Round Pick",
        default=st.session_state.trade_picks_team_1_rounds,
        help="Select draft pick rounds Team 1 is trading away"
    )
    st.session_state.trade_picks_team_1_rounds = trade_picks_team_1_rounds
    trade_picks_team_1 = [DraftPickSimple(r, NEXT_DRAFT_YEAR) for r in trade_picks_team_1_rounds]

    trade_from_team_2 = st.multiselect(
        "Players from Team 2",
        list(team_2_roster.keys()),
        default=st.session_state.trade_from_team_2,
        help="Select players Team 2 is trading away"
    )
    st.session_state.trade_from_team_2 = trade_from_team_2

    trade_picks_team_2_rounds = st.multiselect(
        "Draft Pick Rounds from Team 2",
        options=list(range(1, DRAFT_ROUNDS + 1)),
        format_func=lambda r: f"{NEXT_DRAFT_YEAR} {r}{'th' if r>3 else ['st','nd','rd'][r-1]} Round Pick",
        default=st.session_state.trade_picks_team_2_rounds,
        help="Select draft pick rounds Team 2 is trading away"
    )
    st.session_state.trade_picks_team_2_rounds = trade_picks_team_2_rounds
    trade_picks_team_2 = [DraftPickSimple(r, NEXT_DRAFT_YEAR) for r in trade_picks_team_2_rounds]

    # Prepare player lists
    team_1_players = [team_1_roster[name] for name in trade_from_team_1]
    team_2_players = [team_2_roster[name] for name in trade_from_team_2]

    # Calculate trade values based on mode
    team_1_value = calculate_trade_value(team_1_players, trade_picks_team_1, pick_valuator, st.session_state.pick_value_mode, team_1.team_id)
    team_2_value = calculate_trade_value(team_2_players, trade_picks_team_2, pick_valuator, st.session_state.pick_value_mode, team_2.team_id)

    # Show summary and verdict
    st.markdown(f"### Trade Value Summary")
    st.write(f"Team 1 Value: **{team_1_value:.2f}**")
    st.write(f"Team 2 Value: **{team_2_value:.2f}**")

    if team_1_value > team_2_value:
        st.success("Trade favors Team 1")
    elif team_2_value > team_1_value:
        st.success("Trade favors Team 2")
    else:
        st.info("Trade values are balanced")

with tab_search:
    st.header("🔍 Player Search")
    query = st.text_input("Search player by name")

    if query:
        lower_query = query.lower()
        matching_players = []
        for team in league.teams:
            for player in team.roster:
                if lower_query in player.name.lower():
                    matching_players.append(player)
        if matching_players:
            for p in matching_players:
                value = get_dynasty_value(p)
                st.write(f"**{p.name}** - Dynasty Value: {value}")
        else:
            st.write("No matching players found.")
