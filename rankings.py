# rankings.py

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def clean_name(name):
    """Normalize player name for matching."""
    return re.sub(r'\s*\(.*?\)', '', name).strip().lower()

def fetch_razzball_hitters():
    url = "https://razzball.com/top-500-dynasty-baseball-rankings/"
    print(f"Fetching Razzball Hitters from {url}")
    tables = pd.read_html(url)
    df = tables[0]
    df = df.rename(columns={
        df.columns[0]: "Rank",
        df.columns[1]: "Player",
        df.columns[2]: "Team",
        df.columns[3]: "Position"
    })
    df["source"] = "razzball"
    return df[["Player", "Rank", "Position", "source"]]

def fetch_razzball_pitchers():
    url = "https://razzball.com/top-100-starting-pitchers-dynasty/"
    print(f"Fetching Razzball Pitchers from {url}")
    tables = pd.read_html(url)
    df = tables[0]
    df = df.rename(columns={df.columns[1]: "Player", df.columns[2]: "Position"})
    df["source"] = "razzball"
    return df[["Player", df.columns[0], "Position", "source"]].rename(columns={df.columns[0]: "Rank"})

def fetch_fantasypros_hitters():
    url = "https://www.fantasypros.com/mlb/rankings/dynasty-overall.php"
    print(f"Fetching FantasyPros Hitters from {url}")
    tables = pd.read_html(url)
    df = tables[0]
    df["Position"] = df["POS"]
    df["source"] = "fantasypros"
    return df[["Player", "Rank", "Position", "source"]]

def fetch_fantasypros_pitchers():
    url = "https://www.fantasypros.com/mlb/rankings/dynasty-overall.php"
    print(f"Fetching FantasyPros Pitchers from {url}")
    return fetch_fantasypros_hitters()  # same table for now

def fetch_hashtagbaseball():
    url = "https://www.hashtagbaseball.com/dynasty-rankings"
    print(f"Fetching Hashtag Baseball from {url}")
    tables = pd.read_html(url)
    df = tables[0]
    df["Position"] = df["POS"]
    df["source"] = "hashtag"
    return df[["Player", "Rank", "Position", "source"]]

def combine_rankings(dfs):
    """
    Combine multiple ranking DataFrames into a single player dictionary
    using average rank and most common position.
    """
    combined = {}
    for df in dfs:
        for _, row in df.iterrows():
            name_key = clean_name(row["Player"])
            if name_key not in combined:
                combined[name_key] = {
                    "player_name": row["Player"],
                    "position": row["Position"],
                    "ranks": [],
                    "pos_ranks": [],
                }
            try:
                rank = float(row["Rank"])
                combined[name_key]["ranks"].append(rank)
            except:
                continue

    final = {}
    for name, data in combined.items():
        ranks = data["ranks"]
        if not ranks:
            continue
        overall = round(sum(ranks) / len(ranks), 2)
        pos_rank = round(overall / 10, 2)  # rough estimate for simplicity
        final[name] = {
            "player_name": data["player_name"],
            "overall_rank": overall,
            "position_rank": pos_rank,
            "position": data["position"]
        }
    return final

def fetch_statcast_advanced():
    """
    Scrapes a custom advanced stat page to return WAR, OPS, SLG, OPS+.
    Replace the URL and logic as needed to match your real source.
    """
    url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all"
    print(f"Fetching advanced stats from {url}")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # Simulated example – replace with actual stat site or local file
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table")
        rows = table.find_all("tr")[1:]  # Skip header
    except Exception as e:
        print("Failed to fetch advanced stats:", e)
        return {}

    advanced_data = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
        name = clean_name(cols[1].text)
        try:
            advanced_data[name] = {
                "WAR": float(cols[2].text.strip()),
                "OPS": float(cols[3].text.strip()),
                "SLG": float(cols[4].text.strip()),
                "OPS+": float(cols[5].text.strip())
            }
        except:
            continue

    return advanced_data

