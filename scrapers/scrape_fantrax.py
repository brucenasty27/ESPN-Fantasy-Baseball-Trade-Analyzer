import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.fantraxhq.com/category/mlb/mlb-dynasty-rankings/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FantasyTradeAnalyzer/1.0)"
}

def clean_player_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*\)", "", name)
    name = re.sub(r" Jr\.| Sr\.| III| II", "", name)
    return name.strip().lower()

def fetch_fantraxhq_rankings():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        tables = soup.find_all("table")
        if not tables:
            raise RuntimeError("FantraxHQ rankings tables not found")

        all_data = []
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            rows = table.find_all("tr")[1:]  # skip header row

            # Try to detect positional rank column index (optional)
            pos_rank_idx = None
            for idx, h in enumerate(headers):
                if "pos rank" in h or "position rank" in h:
                    pos_rank_idx = idx
                    break

            stat_cols = ["hr", "r", "rbi", "sb", "bb", "avg", "w", "sv", "k", "era", "whip"]

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                try:
                    rank = int(cells[0].text.strip())
                except:
                    rank = 0

                player_name = clean_player_name(cells[1].text.strip())
                position = cells[2].text.strip() if len(cells) > 2 else ""

                # Positional rank if available
                if pos_rank_idx is not None and len(cells) > pos_rank_idx:
                    try:
                        pos_rank = int(cells[pos_rank_idx].text.strip())
                    except:
                        pos_rank = 0
                else:
                    pos_rank = 0

                stats = {stat.upper(): 0 for stat in stat_cols}

                # Start stats parsing at column 3, but skip pos_rank column if inside
                start_idx = 3
                col_offset = 0
                for i, stat_col in enumerate(stat_cols):
                    col_idx = start_idx + i + col_offset
                    # Adjust col_idx if pos_rank_idx falls between
                    if pos_rank_idx is not None and col_idx >= pos_rank_idx:
                        col_idx += 1
                    if len(cells) > col_idx:
                        try:
                            val = cells[col_idx].text.strip()
                            stats[stat_col.upper()] = float(val) if val else 0
                        except:
                            stats[stat_col.upper()] = 0

                all_data.append({
                    "name": player_name,
                    "overall_rank": rank,
                    "pos_rank": pos_rank,
                    "position": position,
                    **stats
                })

        df = pd.DataFrame(all_data)
        df["overall_rank"] = pd.to_numeric(df["overall_rank"], errors="coerce").fillna(0).astype(int)
        df["pos_rank"] = pd.to_numeric(df["pos_rank"], errors="coerce").fillna(0).astype(int)

        # Remove duplicates, keep best rank
        df = df.sort_values("overall_rank").drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Warning: Failed to fetch FantraxHQ rankings: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_fantraxhq_rankings()
    if not df.empty:
        df.to_csv("fantraxhq_rankings.csv", index=False)
        print(f"✅ Saved FantraxHQ rankings ({len(df)}) to fantraxhq_rankings.csv")
    else:
        print("❌ No data fetched from FantraxHQ")
