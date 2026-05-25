#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pandas"]
# ///
"""
Animated Premier League Bump Chart Race — Client‑Side Edition

Generates index.html with all season data embedded inline (no fetch needed).
Works both locally (file://) and on GitHub Pages. Run build_data.py first
to populate the data/ directory.
"""

import json
import os


def load_season_data(data_dir="data"):
    manifest = []
    seasons = {}
    manifest_path = os.path.join(data_dir, "seasons.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

    for entry in manifest:
        code = entry["code"]
        path = os.path.join(data_dir, f"season-{code}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                seasons[code] = json.load(f)

    return manifest, seasons


def generate_index_html(output_filename="index.html"):
    manifest, seasons = load_season_data()

    manifest_json = json.dumps(manifest, separators=(",", ":"))
    seasons_json = json.dumps(seasons, separators=(",", ":"))

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Premier League Bump Chart Race</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; overflow: hidden; }
.container { display: flex; flex-direction: column; width: 100vw; height: 100vh; }
.header { flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #e2e8f0; background: #fff; gap: 16px; }
.header-left { display: flex; align-items: baseline; gap: 10px; }
.header-left h1 { font-size: 20px; color: #0f172a; font-weight: 700; white-space: nowrap; }
.header-left .subtitle { font-size: 12px; color: #64748b; }
.header-right { display: flex; align-items: center; gap: 12px; }
#season-select { padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; background: #fff; color: #334155; cursor: pointer; }
#date-display { font-size: 22px; font-weight: 700; color: #334155; min-width: 160px; text-align: center; font-variant-numeric: tabular-nums; }
.controls { display: flex; align-items: center; gap: 6px; }
.controls button { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 14px; color: #334155; transition: background .15s; }
.controls button:hover { background: #e2e8f0; }
.speed-group { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #64748b; }
.speed-group input[type=range] { width: 70px; }
.chart-area { flex: 1; min-height: 0; position: relative; }
.chart-area svg { width: 100%; height: 100%; display: block; }
.loading { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 16px; color: #94a3b8; }
.legend-panel { flex-shrink: 0; padding: 6px 20px; display: flex; flex-wrap: wrap; gap: 4px 14px; border-top: 1px solid #e2e8f0; background: #fff; justify-content: center; align-items: center; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer; padding: 2px 5px; border-radius: 4px; transition: background .15s, opacity .2s; color: #334155; user-select: none; }
.legend-item:hover { background: #e2e8f0; }
.legend-item.dimmed { opacity: 0.35; }
.legend-item.stuck { background: #dbeafe; font-weight: 700; opacity: 1 !important; }
.legend-color { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.relegation-badge { margin-left: 8px; background: rgba(220,38,38,.12); color: #dc2626; border: 1px solid #dc2626; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <h1>Premier League Bump Chart Race</h1>
      <span class="subtitle" id="season-label"></span>
    </div>
    <div class="header-right">
      <select id="season-select"><option value="">Loading…</option></select>
      <span id="date-display">—</span>
      <div class="controls">
        <button id="btn-start" title="Restart">&#x21BA;</button>
        <button id="btn-step-back" title="Step back">&#x276E;</button>
        <button id="btn-play" title="Play/Pause">&#x25B6;</button>
        <button id="btn-step-fwd" title="Step forward">&#x276F;</button>
        <div class="speed-group">
          <span>Slow</span>
          <input type="range" id="speed-slider" min="0.5" max="4" step="0.5" value="1.5">
          <span>Fast</span>
        </div>
      </div>
    </div>
  </div>

  <div class="chart-area" id="chart"><div class="loading">Loading season data…</div></div>

  <div class="legend-panel" id="legend">
    <span class="relegation-badge">18–20 = Relegation Zone</span>
  </div>
</div>

<script>
const SEASONS_MANIFEST = """ + manifest_json + """;
const SEASONS_DATA = """ + seasons_json + """;

(function() {
  const container = document.getElementById('chart');
  const legendEl = document.getElementById('legend');
  const dateDisplay = document.getElementById('date-display');
  const seasonSelect = document.getElementById('season-select');
  const seasonLabel = document.getElementById('season-label');
  const btnPlay = document.getElementById('btn-play');

  let DATA = null;
  let margin = { top: 20, right: 200, bottom: 40, left: 60 };
  let width, height;
  let svg, g;
  let xScale, yScale;
  let currentDateIdx = 0;
  let playing = false;
  let speed = 1.5;
  let animationTimer = null;
  let markersGroup;
  let stickySet = new Set();

  function resize() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    if (width < 100 || height < 100) return;
    margin.right = Math.max(150, width * 0.15);
    d3.select('#chart svg').remove();
    if (!DATA) return;
    svg = d3.select('#chart').append('svg')
      .attr('viewBox', [0, 0, width, height]);
    draw();
  }

  function draw() {
    if (!DATA || !svg) return;
    svg.selectAll('*').remove();
    g = svg.append('g');
    g.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var plotW = width - margin.left - margin.right;
    var plotH = height - margin.top - margin.bottom;

    yScale = d3.scaleLinear().domain([0.5, DATA.numTeams + 0.5]).range([0, plotH]);
    xScale = d3.scalePoint().domain(DATA.dates).range([0, plotW]);

    var gridG = g.append('g');
    for (var r = 1; r <= DATA.numTeams; r++) {
      gridG.append('line')
        .attr('x1', 0).attr('x2', plotW)
        .attr('y1', yScale(r)).attr('y2', yScale(r))
        .attr('stroke', r >= 18 ? '#fecaca' : '#e2e8f0')
        .attr('stroke-width', r >= 18 ? 2 : 0.5);
    }
    gridG.append('line')
      .attr('x1', 0).attr('x2', plotW)
      .attr('y1', yScale(17.5)).attr('y2', yScale(17.5))
      .attr('stroke', '#dc2626').attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,4');

    var yLabelG = g.append('g');
    for (var r = 1; r <= DATA.numTeams; r++) {
      yLabelG.append('text')
        .attr('x', -8).attr('y', yScale(r))
        .attr('text-anchor', 'end').attr('alignment-baseline', 'middle')
        .attr('font-size', '11px').attr('fill', r >= 18 ? '#dc2626' : '#94a3b8')
        .text(r);
    }

    var xAxisGroup = g.append('g');
    xAxisGroup.attr('transform', 'translate(0,' + (plotH + 10) + ')');
    var step = Math.max(1, Math.floor(DATA.dates.length / 15));
    DATA.dates.forEach(function(d, i) {
      if (i % step !== 0) return;
      xAxisGroup.append('text')
        .attr('x', xScale(d)).attr('y', 0)
        .attr('text-anchor', 'middle').attr('font-size', '9px').attr('fill', '#94a3b8')
        .text(d.slice(5));
    });

    markersGroup = g.append('g');
    DATA.teams.forEach(function(team) {
      var mg = markersGroup.append('g').attr('class', 'marker-group');
      mg.append('circle')
        .attr('r', 12).attr('fill', '#fff')
        .attr('stroke', DATA.teamColors[team]).attr('stroke-width', 3);
      mg.append('text')
        .attr('text-anchor', 'middle').attr('alignment-baseline', 'middle')
        .attr('font-size', '9px').attr('font-weight', '700')
        .attr('fill', DATA.teamColors[team])
        .text(DATA.teamAbbrs[team]);
    });

    updateMarkers(true);
  }

  function updateMarkers(instant) {
    if (!DATA) return;
    var date = DATA.dates[currentDateIdx];
    var duration = instant ? 0 : 300 / speed;
    dateDisplay.textContent = date;

    markersGroup.selectAll('.marker-group').data(DATA.teams).each(function(team) {
      var rank = DATA.rankings[team][currentDateIdx];
      d3.select(this).transition().duration(duration).ease(d3.easeQuadInOut)
        .attr('transform', 'translate(' + xScale(date) + ',' + yScale(rank) + ')');
    });
  }

  function applySticky() {
    if (!markersGroup) return;
    if (stickySet.size === 0) {
      markersGroup.selectAll('.marker-group').style('opacity', '1');
      legendEl.querySelectorAll('.legend-item').forEach(function(el) {
        el.classList.remove('dimmed', 'stuck');
      });
    } else {
      markersGroup.selectAll('.marker-group').each(function(t, j) {
        d3.select(this).style('opacity', stickySet.has(j) ? '1' : '0.06');
      });
      legendEl.querySelectorAll('.legend-item').forEach(function(el, j) {
        el.classList.toggle('dimmed', !stickySet.has(j));
        el.classList.toggle('stuck', stickySet.has(j));
      });
    }
  }

  function buildLegend() {
    var badge = legendEl.querySelector('.relegation-badge');
    legendEl.innerHTML = '';
    legendEl.appendChild(badge);

    DATA.teams.forEach(function(team, i) {
      var div = document.createElement('div');
      div.className = 'legend-item';
      div.innerHTML = '<span class="legend-color" style="background:' + DATA.teamColors[team] + '"></span><span>' + DATA.teamAbbrs[team] + '</span>';
      div.addEventListener('mouseenter', function() {
        markersGroup.selectAll('.marker-group').each(function(t, j) {
          d3.select(this).style('opacity', j === i ? '1' : '0.04');
        });
        legendEl.querySelectorAll('.legend-item').forEach(function(el, j) {
          el.classList.toggle('dimmed', j !== i);
        });
      });
      div.addEventListener('mouseleave', applySticky);
      div.addEventListener('click', function() {
        if (stickySet.has(i)) stickySet.delete(i);
        else stickySet.add(i);
        applySticky();
      });
      legendEl.appendChild(div);
    });
  }

  function playStep() {
    if (!playing || !DATA) return;
    currentDateIdx++;
    if (currentDateIdx >= DATA.dates.length) {
      currentDateIdx = 0;
    }
    updateMarkers(false);
    scheduleNext();
  }

  function scheduleNext() {
    if (animationTimer) clearTimeout(animationTimer);
    animationTimer = setTimeout(playStep, 400 / speed);
  }

  function togglePlay() {
    playing = !playing;
    btnPlay.textContent = playing ? '\u23F8' : '\u25B6';
    if (playing) scheduleNext();
    else clearTimeout(animationTimer);
  }

  function restart() {
    currentDateIdx = 0;
    playing = false;
    btnPlay.textContent = '\u25B6';
    clearTimeout(animationTimer);
    updateMarkers(true);
  }

  function stepForward() {
    if (!DATA) return;
    if (currentDateIdx < DATA.dates.length - 1) {
      currentDateIdx++;
      updateMarkers(false);
    }
  }

  function stepBack() {
    if (currentDateIdx > 0) {
      currentDateIdx--;
      updateMarkers(false);
    }
  }

  function updateSpeed() {
    speed = +document.getElementById('speed-slider').value;
    if (playing) { clearTimeout(animationTimer); scheduleNext(); }
  }

  function loadSeason(code) {
    var json = SEASONS_DATA[code];
    if (!json) {
      document.getElementById('chart').innerHTML = '<div class="loading" style="color:#dc2626">Season data not found.</div>';
      return;
    }
    document.getElementById('chart').innerHTML = '';
    DATA = json;
    stickySet.clear();
    currentDateIdx = 0;
    playing = false;
    btnPlay.textContent = '\u25B6';
    clearTimeout(animationTimer);
    seasonLabel.textContent = json.label + ' Season';
    resize();
    buildLegend();
    applySticky();
  }

  // Populate season selector
  var seasons = SEASONS_MANIFEST.slice().reverse();
  seasonSelect.innerHTML = '';
  seasons.forEach(function(s) {
    var opt = document.createElement('option');
    opt.value = s.code;
    opt.textContent = s.label;
    seasonSelect.appendChild(opt);
  });
  var latest = seasons[0] ? seasons[0].code : '2526';
  seasonSelect.value = latest;
  loadSeason(latest);

  seasonSelect.addEventListener('change', function() {
    loadSeason(seasonSelect.value);
  });

  btnPlay.addEventListener('click', togglePlay);
  document.getElementById('btn-start').addEventListener('click', restart);
  document.getElementById('btn-step-back').addEventListener('click', stepBack);
  document.getElementById('btn-step-fwd').addEventListener('click', stepForward);
  document.getElementById('speed-slider').addEventListener('input', updateSpeed);
  window.addEventListener('resize', resize);
})();
</script>
</body>
</html>
"""
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated '{output_filename}' with {len(manifest)} seasons embedded ({len(html)} bytes)")


def main():
    generate_index_html()
    print("Run build_data.py first to populate data/ then run this script")


if __name__ == "__main__":
    main()
