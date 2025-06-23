import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import unicodedata


def normalize_name(name):
    """Normalize and clean player names for matching."""
    name = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode()
    return re.sub(r'\W+', '', name).lower()


def fetch_razzball_hitters(url="https://razzball.com/mlbhittingstats/"):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))[0]
    df['overall_rank'] = range(1, len(df) + 1)
    df['pos_rank'] = df.groupby('Pos')['overall_rank'].rank(method='first').astype(int)
    df = df.rename(columns={'Name': 'name', 'Pos': 'position'})
    return df[['name', 'overall_rank', 'pos_rank', 'position']]


def fetch_razzball_pitchers(url="https://razzball.com/mlbpitchingstats/"):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))[0]
    df['overall_rank'] = range(1, len(df) + 1)
    df['pos_rank'] = df.groupby('Pos')['overall_rank'].rank(method='first').astype(int)
    df = df.rename(columns={'Name': 'name', 'Pos': 'position'})
    return df[['name', 'overall_rank', 'pos_rank', 'position']]


def fetch_fantasypros_hitters(url="https://www.fantasypros.com/mlb/rankings/dynasty-hitters.php"):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))[0]
    df = df.rename(columns={
        'Player': 'name',
        'Overall Rank': 'overall_rank',
        'Pos Rank': 'pos_rank',
        'Pos': 'position'
    })
    df = df[['name', 'overall_rank', 'pos_rank', 'position']]
    df['overall_rank'] = pd.to_numeric(df['overall_rank'], errors='coerce').fillna(999).astype(int)
    df['pos_rank'] = pd.to_numeric(df['pos_rank'], errors='coerce').fillna(99).astype(int)
    return df


def fetch_fantasypros_pitchers(url="https://www.fantasypros.com/mlb/rankings/dynasty-pitchers.php"):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))[0]
    df = df.rename(columns={
        'Player': 'name',
        'Overall Rank': 'overall_rank',
        'Pos Rank': 'pos_rank',
        'Pos': 'position'
    })
    df = df[['name', 'overall_rank', 'pos_rank', 'position']]
    df['overall_rank'] = pd.to_numeric(df['overall_rank'], errors='coerce').fillna(999).astype(int)
    df['pos_rank'] = pd.to_numeric(df['pos_rank'], errors='coerce').fillna(99).astype(int)
    return df


def fetch_hashtagbaseball(url="https://hashtagbaseball.com/fantasy-baseball-projections"):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))[0]
    df = df.rename(columns={'Player': 'name', 'Pos': 'position'})
    df['overall_rank'] = range(1, len(df) + 1)
    df['pos_rank'] = df.groupby('position')['overall_rank'].rank(method='first').astype(int)
    return df[['name', 'overall_rank', 'pos_rank', 'position']]


def combine_rankings(dfs):
    """Combine multiple rankings DataFrames into a unified dictionary."""
    combined = {}
    for df in dfs:
        for _, row in df.iterrows():
            norm_name = normalize_name(row['name'])
            if norm_name not in combined:
                combined[norm_name] = {
                    'name': row['name'],
                    'overall_ranks': [],
                    'pos_ranks': [],
                    'positions': []
                }
            combined[norm_name]['overall_ranks'].append(row['overall_rank'])
            combined[norm_name]['pos_ranks'].append(row['pos_rank'])
            combined[norm_name]['positions'].append(row['position'])

    averaged = {}
    for norm_name, data in combined.items():
        avg_overall = round(sum(data['overall_ranks']) / len(data['overall_ranks']))
        avg_pos = round(sum(data['pos_ranks']) / len(data['pos_ranks']))
        primary_pos = data['positions'][0]
        averaged[norm_name] = {
            'name': data['name'],
            'overall_rank': avg_overall,
            'pos_rank': avg_pos,
            'position': primary_pos
        }
    return averaged
