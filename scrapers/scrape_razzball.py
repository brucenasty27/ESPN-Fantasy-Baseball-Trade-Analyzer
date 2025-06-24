import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def clean_name(name):
    name = re.sub(r"\\s*\\(.*?\\)", "", name)
    name = re.sub(r" Jr\\.| Sr\\.| III| II", "", name)
    return name.strip().lower()

def scrape_razzball_table(url):
    try:
        tables = pd.read_html(url)
        if not tables:
            print(f"No tables found on {url}")
            return pd.DataFrame()
        df = tables[0]
        return df
    except Exception as e:
        print(f"Error reading {url}: {e}")
        return pd.DataFrame()

def process_hitters(df):
    df = df.rename(columns=str.lower)
    df = df.rename(columns={"player": "name"})
    df = df[[col for col in df.columns if col in ["name", "team", "pos", "ops", "slg", "war"]]]
    df["position"] = df["pos"]
    df.drop(columns=["pos"], inplace=True, errors='ignore')
    df["player_type"] = "hitter"
    df["source"] = "razzball"
    df["name"] = df["name"].astype(str).apply(clean_name)
    return df

def process_pitchers(df):
    df = df.rename(columns=str.lower)
    df = df.rename(columns={"player": "name"})
    df = df[[col for col in df.columns if col in ["name", "team", "k/9", "era", "whip", "war"]]]
    df["position"] = "P"
    df["player_type"] = "pitcher"
    df["source"] = "razzball"
    df["name"] = df["name"].astype(str).apply(clean_name)
    return df

def main():
    hitting_url = "https://razzball.com/mlbhittingstats/"
    pitching_url = "https://razzball.com/mlbpitchingstats/"

    hitters_raw = scrape_razzball_table(hitting_url)
    pitchers_raw = scrape_razzball_table(pitching_url)

    hitters = process_hitters(hitters_raw) if not hitters_raw.empty else pd.DataFrame()
    pitchers = process_pitchers(pitchers_raw) if not pitchers_raw.empty else pd.DataFrame()

    combined = pd.concat([hitters, pitchers], ignore_index=True)

    if not combined.empty:
        combined.to_csv("razzball_stats.csv", index=False)
        print("✅ Razzball stats saved to razzball_stats.csv")
    else:
        print("⚠️ No data to save.")

if __name__ == "__main__":
    main()
