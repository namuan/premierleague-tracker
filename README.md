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

All 20 seasons (2006–07 to 2025–26) are embedded directly in the HTML — no network requests needed after page load. The chart works locally (`file://`) and on any static host.

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
Push `index.html`. One file, zero dependencies. Enable GitHub Pages on the repo — no build step needed.

## Project structure

```
relegation-tracker/
├── index.html            # Self-contained chart (all data embedded)
├── data/                 # Source JSON (for rebuilding)
│   ├── seasons.json
│   └── season-XXXX.json
├── build_data.py         # Downloads & computes season data
├── bump_chart_race.py    # Generates index.html from data/
└── README.md
```

## Thanks

Match data generously provided by [football-data.co.uk](https://www.football-data.co.uk/), a free historical football results and betting odds archive maintained by Joseph Buchdahl.

## License

[MIT](LICENSE)
