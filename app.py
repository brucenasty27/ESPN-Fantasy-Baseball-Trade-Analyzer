import streamlit as st
from espn_api.baseball import League
from draft_value import DraftPickValuator, DraftPickSimple
from dataclasses import dataclass
import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import openai
import logging

from rankings import fetch_all_sources, combine_rankings, clean_player_name
from player_value import get_dynasty_value, get_simple_draft_pick_value

# Load environment variables from .env file
load_dotenv()

# Configure logging for debug
logging.basicConfig(level=logging.INFO)

# Validate environment variables
try:
    LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
    SEASON_YEAR = int(os.getenv("SEASON_YEAR"))
    SWID = os.getenv("SWID")
    ESPN_S2 = os.getenv("ESPN_S2")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not (SWID and ESPN_S2):
        raise ValueError("Missing SWID or ESPN_S2 tokens")
    if not OPENAI_API_KEY:
        raise ValueError("Missing OpenAI API key")
except Exception as e:
    st.error(f"Error loading environment variables: {e}")
    st.stop()

openai.api_key = OPENAI_API_KEY

st.set_page_config(page_title="Dynasty Trade Analyzer", layout="wide")
st.title("🏆 Dynasty Trade Analyzer with Draft Picks")

DRAFT_ROUNDS = 16
NEXT_DRAFT_YEAR = SEASON_YEAR + 1

@dataclass
class DraftPickSimple:
    round_number: int
    year: int

    def __str__(self):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(
            self.round_number if self.round_number < 20 else 0, "th"
        )
        return f"{self.year} {self.round_number}{suffix} Round Pick"

@st.cache_resource(show_spinner=False)
def load_league_cached():
    logging.info("Loading ESPN League data...")
    try:
        league = League(league_id=LEAGUE_ID, year=SEASON_YEAR, swid=SWID, espn_s2=ESPN_S2)
        logging.info("League loaded successfully.")
        return league
    except Exception as e:
        logging.error(f"Failed to load league: {e}")
        return None

@st.cache_data
def load_rankings_csv(file_path="data/dynasty_rankings_cleaned.csv"):
    if not os.path.exists(file_path):
        st.warning(f"⚠️ Missing rankings file: {file_path}. Please run the ranking update workflow.")
        return pd.DataFrame(columns=["name"])
    try:
        df = pd.read_csv(file_path)
        if "name" not in df.columns:
            st.warning(f"⚠️ Rankings CSV missing 'name' column: {file_path}")
            return pd.DataFrame(columns=["name"])
        df["name"] = df["name"].astype(str).str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Failed to load rankings CSV {file_path}: {e}")
        return pd.DataFrame(columns=["name"])

def get_team_logo(team):
    logo = getattr(team, "logo_url", "")
    if not logo:
        logo = "https://via.placeholder.com/75?text=No+Logo"
    return logo

def calculate_trade_value(players, picks, pick_valuator=None, mode="simple", team_id=None):
    player_value = sum(get_dynasty_value(clean_player_name(p.name)) for p in players)
    if mode == "advanced" and pick_valuator and team_id is not None:
        picks_value = sum(pick_valuator.get_pick_value(team_id, p.round_number) for p in picks)
    else:
        picks_value = sum(get_simple_draft_pick_value(p) for p in picks)
    return player_value + picks_value

def refresh_rankings():
    try:
        st.info("Refreshing dynasty rankings (this may take a moment)...")
        dfs = fetch_all_sources(load_league_cached())
        df = combine_rankings(dfs)
        output_path = os.path.join("data", "dynasty_rankings_cleaned.csv")
        df.to_csv(output_path, index=False)
        return "✅ Dynasty rankings refreshed and saved."
    except Exception as e:
        return f"Error refreshing rankings: {e}"

def ai_trade_verdict(team1_name, team2_name, players_1, players_2, value_1, value_2):
    try:
        msg = f"Team 1 ({team1_name}) trades {', '.join([p.name for p in players_1])}. "
        msg += f"Team 2 ({team2_name}) trades {', '.join([p.name for p in players_2])}. "
        msg += f"Team 1 value: {value_1:.2f}, Team 2 value: {value_2:.2f}. Who wins the trade? Suggest fair modifications if any."

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fantasy baseball expert analyzing trade fairness."},
                {"role": "user", "content": msg}
            ],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"AI verdict unavailable: {e}"

# Initialize or load league once and store in session state
if "league" not in st.session_state:
    league = load_league_cached()
    if league is None:
        st.error("Failed to load league data. Please check your ESPN credentials and network.")
        st.stop()
    st.session_state.league = league
else:
    league = st.session_state.league

rankings_df = load_rankings_csv()

# Initialize session state variables if missing
for key in ["trade_from_team_1", "trade_from_team_2", "trade_picks_team_1_rounds", "trade_picks_team_2_rounds"]:
    if key not in st.session_state:
        st.session_state[key] = []

if "pick_value_mode" not in st.session_state:
    st.session_state.pick_value_mode = "simple"
if "last_sync" not in st.session_state:
    st.session_state.last_sync = None

with st.sidebar:
    st.header("Settings")

    if st.button("🔄 Refresh Dynasty Rankings Now"):
        with st.spinner("Refreshing dynasty rankings..."):
            output = refresh_rankings()
            st.success(output)

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
            league = load_league_cached()
            if league is None:
                st.error("Failed to reload league data.")
            else:
                st.session_state.league = league
                st.session_state.last_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"✅ League data synced at {st.session_state.last_sync}")

if st.session_state.last_sync:
    st.caption(f"Last synced: {st.session_state.last_sync}")

team_names = [team.team_name for team in league.teams]

pick_valuator = None
if st.session_state.pick_value_mode == "advanced":
    standings_team_ids = [team.team_id for team in sorted(league.teams, key=lambda t: t.wins)]
    pick_valuator = DraftPickValuator(standings_team_ids)

def pick_suffix(n):
    return {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else 0, "th")

draft_pick_options = [f"{NEXT_DRAFT_YEAR} {rnd}{pick_suffix(rnd)} Round Pick" for rnd in range(1, DRAFT_ROUNDS + 1)]

def parse_pick_string(pick_str):
    parts = pick_str.split()
    round_str = parts[1]
    for suffix in ["st", "nd", "rd", "th"]:
        if round_str.endswith(suffix):
            round_str = round_str[:-len(suffix)]
            break
    return int(round_str)

tab_trade, tab_search, tab_compare = st.tabs(["Trade Analyzer", "Player Search", "Player Comparison"])

with tab_trade:
    st.header("🤝 Trade Analyzer")

    col1, col2 = st.columns(2)
    team_1_name = col1.selectbox("Select Team 1", team_names)
    team_2_name = col2.selectbox("Select Team 2", team_names, index=1 if len(team_names) > 1 else 0)

    team_1 = next(t for t in league.teams if t.team_name == team_1_name)
    team_2 = next(t for t in league.teams if t.team_name == team_2_name)

    col1.image(get_team_logo(team_1), width=75)
    col2.image(get_team_logo(team_2), width=75)

    roster_1 = {p.name: p for p in team_1.roster}
    roster_2 = {p.name: p for p in team_2.roster}

    trade_from_team_1 = st.multiselect("Players from Team 1", list(roster_1.keys()))
    trade_from_team_2 = st.multiselect("Players from Team 2", list(roster_2.keys()))

    draft_picks_team_1 = st.multiselect("Team 1 Draft Picks", options=draft_pick_options)
    draft_picks_team_2 = st.multiselect("Team 2 Draft Picks", options=draft_pick_options)

    players_1 = [roster_1[name] for name in trade_from_team_1 if name in roster_1]
    players_2 = [roster_2[name] for name in trade_from_team_2 if name in roster_2]

    picks_1 = [DraftPickSimple(parse_pick_string(pick_str), NEXT_DRAFT_YEAR) for pick_str in draft_picks_team_1]
    picks_2 = [DraftPickSimple(parse_pick_string(pick_str), NEXT_DRAFT_YEAR) for pick_str in draft_picks_team_2]

    value_1 = calculate_trade_value(players_1, picks_1, pick_valuator, st.session_state.pick_value_mode, team_1.team_id)
    value_2 = calculate_trade_value(players_2, picks_2, pick_valuator, st.session_state.pick_value_mode, team_2.team_id)

    st.markdown("### Trade Value Summary")
    st.write(f"{team_1_name}: **{value_1:.2f}**")
    st.write(f"{team_2_name}: **{value_2:.2f}**")

    max_val = max(value_1, value_2) if max(value_1, value_2) > 0 else 1
    team1_pct = value_1 / max_val
    team2_pct = value_2 / max_val

    bar_html = f"""
    <div style='display: flex; width: 100%; height: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden;'>
        <div style='width: {team1_pct * 100:.1f}%; background-color: #4caf50;'></div>
        <div style='width: {team2_pct * 100:.1f}%; background-color: #f44336;'></div>
    </div>
    """
    st.markdown(bar_html, unsafe_allow_html=True)

    if value_1 > value_2:
        st.success("Trade favors Team 1")
    elif value_2 > value_1:
        st.success("Trade favors Team 2")
    else:
        st.info("Trade is balanced")

    if st.button("🤖 AI Trade Verdict & Suggestions"):
        with st.spinner("Analyzing with AI..."):
            verdict = ai_trade_verdict(team_1_name, team_2_name, players_1, players_2, value_1, value_2)
            st.markdown("### 🤖 Who Says No?")
            st.write(verdict)

with tab_compare:
    st.header("🔍 Player Comparison Tool")

    all_players = sorted(rankings_df["name"].unique()) if not rankings_df.empty else []
    col1, col2 = st.columns(2)

    p1_name = col1.selectbox("Player 1", all_players)
    p2_name = col2.selectbox("Player 2", all_players, index=1 if len(all_players) > 1 else 0)

    def get_player_stats(name):
        if not name or rankings_df.empty:
            return {}
        row = rankings_df[rankings_df["name"] == name.lower()]
        if row.empty:
            return {}
        return row.squeeze().to_dict()

    stats1 = get_player_stats(p1_name)
    stats2 = get_player_stats(p2_name)

    if stats1 and stats2:
        stat_keys = ["overall_rank", "pos_rank", "dynasty_value", "HR", "R", "RBI", "SB", "BB", "AVG", "W", "SV", "K", "ERA", "WHIP"]
        st.markdown("### Stat Comparison")
        for key in stat_keys:
            val1 = stats1.get(key, 0)
            val2 = stats2.get(key, 0)
            highlight1 = "font-weight: bold; background-color: #e6e6e6;" if val1 > val2 else ""
            highlight2 = "font-weight: bold; background-color: #e6e6e6;" if val2 > val1 else ""
            row_html = f"""
            <div style='display: flex; justify-content: space-between; padding: 4px 0;'>
                <div style='width: 45%; {highlight1}'>{val1}</div>
                <div style='width: 10%; text-align: center;'>{key}</div>
                <div style='width: 45%; text-align: right; {highlight2}'>{val2}</div>
            </div>
            """
            st.markdown(row_html, unsafe_allow_html=True)
    else:
        st.warning("One or both players not found in rankings data.")
