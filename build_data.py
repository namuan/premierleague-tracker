#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pandas"]
# ///
"""Build pre-computed ranking JSON files for all available EPL seasons.

Downloads CSV data from football-data.co.uk, computes rolling match-by-match
rankings, and saves compact JSON files to data/season-XXXX.json.
"""

import json
import os
import pandas as pd

DATA_DIR = "data"
SEASON_CODES = [
    "0607", "0708", "0809",
    "0910", "1011", "1112", "1213", "1314", "1415",
    "1516", "1617", "1718", "1819", "1920", "2021",
    "2122", "2223", "2324", "2425", "2526",
]

TEAM_ABBREVIATIONS = {
    "Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU",
    "Brentford": "BRE", "Brighton": "BHA", "Burnley": "BUR",
    "Cardiff": "CAR", "Chelsea": "CHE", "Crystal Palace": "CRY",
    "Everton": "EVE", "Fulham": "FUL", "Huddersfield": "HUD",
    "Hull": "HUL", "Ipswich": "IPS", "Leeds": "LEE",
    "Leicester": "LEI", "Liverpool": "LIV", "Luton": "LUT",
    "Man City": "MCI", "Man United": "MUN", "Middlesbrough": "MID",
    "Newcastle": "NEW", "Norwich": "NOR", "Nott'm Forest": "NFO",
    "Portsmouth": "POR", "QPR": "QPR", "Reading": "REA",
    "Sheffield United": "SHU", "Southampton": "SOU",
    "Stoke": "STK", "Sunderland": "SUN", "Swansea": "SWA",
    "Tottenham": "TOT", "Watford": "WAT", "West Brom": "WBA",
    "West Ham": "WHU", "Wigan": "WIG", "Wolves": "WOL",
    "Charlton": "CHA", "Birmingham": "BIR", "Blackburn": "BLB",
    "Blackpool": "BLP", "Bolton": "BOL", "Derby": "DER",
    "Sheffield Weds": "SHW", "Bradford": "BRD", "Coventry": "COV",
    "Oldham": "OLD", "Swindon": "SWI", "Wimbledon": "WIM",
    "Port Vale": "PTV", "Barnsley": "BAR",
}

OFFICIAL_COLORS = {
    "Arsenal": "#EF0107", "Aston Villa": "#670E36", "Bournemouth": "#B50E12",
    "Brentford": "#E30613", "Brighton": "#0057B8", "Burnley": "#6C1D45",
    "Cardiff": "#0070B5", "Chelsea": "#034694", "Crystal Palace": "#1B458F",
    "Everton": "#003399", "Fulham": "#000000", "Huddersfield": "#0E63AD",
    "Hull": "#F5A12D", "Ipswich": "#0000FF", "Leeds": "#1D428A",
    "Leicester": "#003090", "Liverpool": "#C8102E", "Luton": "#F47421",
    "Man City": "#6CABDD", "Man United": "#DA291C", "Middlesbrough": "#DA291C",
    "Newcastle": "#241F20", "Norwich": "#00A650", "Nott'm Forest": "#DD0000",
    "Portsmouth": "#001489", "QPR": "#0166B1", "Reading": "#004494",
    "Sheffield United": "#EF0107", "Southampton": "#D71920",
    "Stoke": "#E03A3E", "Sunderland": "#FF0000", "Swansea": "#121212",
    "Tottenham": "#132257", "Watford": "#FBEE23", "West Brom": "#122F67",
    "West Ham": "#7A263A", "Wigan": "#0053A1", "Wolves": "#FDB913",
    "Charlton": "#CC0000", "Birmingham": "#1269AE", "Blackburn": "#006EB3",
    "Blackpool": "#E85903", "Bolton": "#00333D", "Derby": "#000000",
    "Sheffield Weds": "#0166B1", "Bradford": "#85002D", "Coventry": "#00B2A9",
    "Oldham": "#004B8D", "Swindon": "#DF0101", "Wimbledon": "#01216B",
    "Port Vale": "#00393A", "Barnsley": "#CC0000",
    "DEFAULT": "#94A3B8",
}


def calculate_rolling_rankings(df):
    df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].dropna()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date']).sort_values(by='Date').reset_index(drop=True)

    teams = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
    standings = {team: {'points': 0, 'gd': 0, 'gs': 0, 'name': team} for team in teams}

    unique_dates = sorted(df['Date'].unique())
    history = []

    for current_date in unique_dates:
        matches_today = df[df['Date'] == current_date]
        for _, match in matches_today.iterrows():
            home, away = match['HomeTeam'], match['AwayTeam']
            fthg, ftag = int(match['FTHG']), int(match['FTAG'])
            standings[home]['gs'] += fthg
            standings[away]['gs'] += ftag
            standings[home]['gd'] += (fthg - ftag)
            standings[away]['gd'] += (ftag - fthg)
            if fthg > ftag:
                standings[home]['points'] += 3
            elif ftag > fthg:
                standings[away]['points'] += 3
            else:
                standings[home]['points'] += 1
                standings[away]['points'] += 1

        sorted_teams = sorted(
            standings.values(),
            key=lambda x: (x['points'], x['gd'], x['gs'], [-ord(c) for c in x['name']]),
            reverse=True,
        )
        for rank_idx, team_data in enumerate(sorted_teams, start=1):
            history.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Team': team_data['name'],
                'Rank': rank_idx,
            })

    return pd.DataFrame(history)


def build_season_json(code):
    url = f"https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
    print(f"  Fetching {url} ...")
    try:
        raw = pd.read_csv(url, encoding='latin-1', on_bad_lines='skip')
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return None

    rankings = calculate_rolling_rankings(raw)
    pivot = rankings.pivot(index='Date', columns='Team', values='Rank').ffill()
    dates = list(pivot.index)
    teams = list(pivot.columns)

    ranks_data = {}
    for team in teams:
        ranks_data[team] = [int(pivot.loc[date, team]) for date in dates]

    team_colors = {}
    team_abbrs = {}
    for team in teams:
        team_colors[team] = OFFICIAL_COLORS.get(team, OFFICIAL_COLORS["DEFAULT"])
        team_abbrs[team] = TEAM_ABBREVIATIONS.get(team, team[:3].upper())

    year_start = int("20" + code[:2])
    year_end = int("20" + code[2:])
    label = f"{year_start}–{year_end % 100:02d}"

    return {
        "code": code,
        "label": label,
        "dates": dates,
        "teams": teams,
        "rankings": ranks_data,
        "teamColors": team_colors,
        "teamAbbrs": team_abbrs,
        "numTeams": len(teams),
    }


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Build manifest of all seasons
    seasons = []
    for code in SEASON_CODES:
        print(f"Season {code}:")
        data = build_season_json(code)
        if data is None:
            continue
        path = os.path.join(DATA_DIR, f"season-{code}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  ✅ Saved {path} ({len(data['teams'])} teams, {len(data['dates'])} matchdays)")
        seasons.append({"code": code, "label": data["label"], "teams": len(data["teams"])})

    # Save manifest
    manifest_path = os.path.join(DATA_DIR, "seasons.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(seasons, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\n✅ Built {len(seasons)} seasons. Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
