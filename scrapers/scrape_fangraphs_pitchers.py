import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_fangraphs_pitchers():
    url = "https://www.fangraphs.com/projections.aspx?pos=all&stats=pit&type=ros"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        if table is None or not table.find("thead"):
            print("❌ No <thead> found in table. Fangraphs layout may have changed.")
            return pd.DataFrame(columns=["name", "W", "SV", "K", "ERA", "WHIP", "IP", "position"])

        df = pd.read_html(str(table))[0]

        # Clean column names
        df.rename(columns=lambda x: x.strip().lower(), inplace=True)
        df.columns = [col.replace(' ', '_') for col in df.columns]

        # Normalize expected fields
        df["name"] = df["name"].astype(str).str.strip()
        df["position"] = "P"

        expected_cols = ["name", "W", "SV", "K", "ERA", "WHIP", "IP", "position"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0

        return df[expected_cols]

    except Exception as e:
        print(f"Error fetching pitchers from FanGraphs: {e}")
        return pd.DataFrame(columns=["name", "W", "SV", "K", "ERA", "WHIP", "IP", "position"])
