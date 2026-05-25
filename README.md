# Premier League Bump Chart Race

An animated, client-side bump chart race showing team ranking positions across every Premier League matchday since 2006–07.

**[Live demo →](https://namuan.github.io/premierleague-tracker/)**

## Features

- **Animated race** — team position markers slide smoothly across matchdays
- **20 seasons** (2006–07 to 2025–26) — selectable via dropdown
- **Click to stick** teams in the legend; hover to isolate
- **Play/Pause**, step forward/backward, speed control
- **Relegation zone** highlighted in red (positions 18–20)
- **Fully client-side** — zero server dependencies, works on GitHub Pages
- **Team colors** match official Premier League kits

## How it works

Pre-computed ranking data is stored as compact JSON files in `data/` (one file per season, ~7–10 KB each). The page loads the manifest and fetches season data on demand — everything runs in the browser.

## Building locally

### 1. Fetch & compute season data
```bash
uv run build_data.py
```

This downloads CSV match results from [football-data.co.uk](https://www.football-data.co.uk), computes rolling rankings, and saves the results to `data/season-XXXX.json`.

### 2. Generate the HTML page
```bash
uv run bump_chart_race.py
```

This writes `index.html`. The Python scripts only need `pandas` (auto-installed by `uv`).

### 3. Deploy
Push `index.html` and the `data/` directory. Enable GitHub Pages on the repo — no build step needed.

## Project structure

```
relegation-tracker/
├── data/                 # Pre-computed ranking JSON (20 seasons)
│   ├── seasons.json      # Manifest of available seasons
│   └── season-XXXX.json  # One file per season
├── index.html            # The animated bump chart (client-side)
├── build_data.py         # Script to download & compute season data
├── bump_chart_race.py    # Script to generate index.html
└── README.md
```

## Thanks

Match data generously provided by [football-data.co.uk](https://www.football-data.co.uk/), a free historical football results and betting odds archive maintained by Joseph Buchdahl.

## License

[MIT](LICENSE)
