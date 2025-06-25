import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

CBS_URL = "https://www.cbssports.com/fantasy/baseball/rankings/dynasty/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def clean_name(name):
    name = re.sub(r"\s*\(.*?\)", "", name)  # Remove team info in parentheses
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_cbssports_rankings():
    print("Fetching CBS Sports dynasty rankings...")
    try:
        response = requests.get(CBS_URL, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch CBS rankings: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all tables with player data (CBS sometimes splits by position)
    tables = soup.find_all("table")
    if not tables:
        print("❌ No tables found on CBS rankings page")
        return pd.DataFrame()

    dfs = []
    for table in tables:
        try:
            df = pd.read_html(str(table))[0]
            if "Player" not in df.columns:
                continue

            # Rename columns to standardized names, add missing with default 0
            rename_map = {
                "Player": "name",
                "Rank": "overall_rank",
                "HR": "HR",
                "R": "R",
                "RBI": "RBI",
                "SB": "SB",
                "BB": "BB",
                "AVG": "AVG",
                "W": "W",
                "SV": "SV",
                "K": "K",
                "ERA": "ERA",
                "WHIP": "WHIP",
                # Position info if present
                "Pos": "position"
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

            # Clean player names
            df["name"] = df["name"].apply(clean_name)

            # Ensure all needed columns exist, fill missing with 0 or empty string for position
            required_cols = [
                "overall_rank", "HR", "R", "RBI", "SB", "BB", "AVG",
                "W", "SV", "K", "ERA", "WHIP", "position"
            ]
            for col in required_cols:
                if col not in df.columns:
                    if col == "position":
                        df[col] = ""
                    else:
                        df[col] = 0

            # Convert numeric columns to correct types, coerce errors to NaN then fill with 0
            numeric_cols = [
                "overall_rank", "HR", "R", "RBI", "SB", "BB", "AVG",
                "W", "SV", "K", "ERA", "WHIP"
            ]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            dfs.append(df[["name"] + required_cols])
        except Exception as e:
            print(f"Warning: Skipped one table due to error: {e}")

    if not dfs:
        print("❌ No valid player tables parsed")
        return pd.DataFrame()

    final_df = pd.concat(dfs, ignore_index=True)
    final_df.dropna(subset=["name", "overall_rank"], inplace=True)

    print(f"✅ Retrieved {len(final_df)} players from CBS")
    return final_df

if __name__ == "__main__":
    df = fetch_cbssports_rankings()
    df.to_csv("data/cbssports_rankings.csv", index=False)
    print("✅ Saved CBS rankings to data/cbssports_rankings.csv")
