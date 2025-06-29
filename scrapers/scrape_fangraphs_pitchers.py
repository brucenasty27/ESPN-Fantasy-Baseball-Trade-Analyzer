import pandas as pd
import requests
from bs4 import BeautifulSoup

def parse_ip(ip_val):
    try:
        ip_float = float(ip_val)
        whole = int(ip_float)
        fraction = round(ip_float - whole, 1)
        if fraction == 0.1:
            return whole + 1/3
        elif fraction == 0.2:
            return whole + 2/3
        return ip_float
    except:
        return 0.0

def fetch_fangraphs_pitchers():
    url = "https://www.fangraphs.com/projections.aspx?pos=all&stats=pit&type=ros"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        if table is None or not table.find("thead"):
            print("❌ No <thead> found in table. Fangraphs layout may have changed.")
            return pd.DataFrame(columns=["name", "w", "sv", "k", "era", "whip", "ip", "position"])

        df = pd.read_html(str(table))[0]

        # Clean column names: lowercase and underscores
        df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'), inplace=True)

        # Normalize expected fields
        df["name"] = df["name"].astype(str).str.strip()
        df["position"] = "P"

        expected_cols = ["name", "w", "sv", "k", "era", "whip", "ip", "position"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0

        # Convert numeric columns
        num_cols = ["w", "sv", "k", "era", "whip", "ip"]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Parse innings pitched fractional parts properly
        df["ip"] = df["ip"].apply(parse_ip)

        return df[expected_cols]

    except Exception as e:
        print(f"Error fetching pitchers from Fangraphs: {e}")
        return pd.DataFrame(columns=["name", "w", "sv", "k", "era", "whip", "ip", "position"])

if __name__ == "__main__":
    df = fetch_fangraphs_pitchers()
    print(f"Fetched {len(df)} pitchers from Fangraphs")
    df.to_csv("data/fangraphs_pitchers.csv", index=False)
