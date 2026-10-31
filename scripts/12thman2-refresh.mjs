// The 12th Man v2 - daily pool refresh (fresh brief 31 Oct 2026).
// Writes 12th-man/v2/data/pool.json: GENERIC per-player data for the decision
// room. No team IDs, no squads, no personal state - publishable by construction.
// Extends the v1 pool with: recent per-gameweek rows (form/consistency/spike
// evidence), FPL's own ep_next benchmark, official chip windows, event metadata
// and per-team strengths. Projection model unchanged: docs/09 v1 coefficients.

import { mkdir, writeFile } from 'node:fs/promises';

const API = 'https://fantasy.premierleague.com/api';
const OUT_DIR = new URL('../12th-man/v2/data/', import.meta.url);
const TRAILING = 4;
const MIN_TRAILING_MINUTES = 180;
const RECENT_GWS = 8; // per-GW history rows kept for the evidence drawers

// docs/09 v1 coefficients (fit on 2021-22..2024-25, validated on rolling
// holdouts 2024-25 and 2025-26). Unchanged from v1 - a refit must beat this on
// the same protocol before shipping (docs/10).
const COEF = { const: 0.379, pts4: 0.123, pts2: 0.077, xgi4: 1.084, xgi2: 0.613,
  minshare4: 1.542, home: 0.450, ogcAtt: 0.182, ogcDef: 0.104, ogsAtt: -0.118, ogsDef: -0.305 };
const POS_OFFSET = { 1: 0.623, 2: 0.058, 3: 0.0, 4: 0.148 }; // GKP DEF MID FWD

async function j(url) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(url);
      if (r.ok) return r.json();
    } catch (_) {}
    await new Promise((x) => setTimeout(x, 600 * (attempt + 1)));
  }
  throw new Error(`FPL API unavailable: ${url}`);
}

const boot = await j(`${API}/bootstrap-static/`);
const current = boot.events.find((e) => e.is_current) || boot.events.filter((e) => e.finished).at(-1);
const next = boot.events.find((e) => e.is_next) || boot.events.find((e) => !e.finished);

// Official chip windows from the rules data (each chip's valid event range).
const chipWindows = boot.chips.map((c) => ({ name: c.name, number: c.number, start: c.start_event, stop: c.stop_event, type: c.chip_type }));

// Team attacking/defensive strength entering GW `next`: mean goals scored and
// conceded per match over the TRAILING completed gameweeks, from finished scores.
const completedIds = boot.events.filter((e) => e.finished).map((e) => e.id).slice(-TRAILING);
const conceded = new Map(); // team id -> {gc, gs, n}
for (const ev of completedIds) {
  const fx = await j(`${API}/fixtures/?event=${ev}`);
  for (const f of fx) {
    if (!f.finished) continue;
    const h = conceded.get(f.team_h) || { gc: 0, gs: 0, n: 0 };
    h.gc += f.team_a_score; h.gs += f.team_h_score; h.n += 1; conceded.set(f.team_h, h);
    const a = conceded.get(f.team_a) || { gc: 0, gs: 0, n: 0 };
    a.gc += f.team_h_score; a.gs += f.team_a_score; a.n += 1; conceded.set(f.team_a, a);
  }
}
const teamGc4 = new Map([...conceded].map(([t, v]) => [t, v.n ? v.gc / v.n : 1.4]));
const teamGs4 = new Map([...conceded].map(([t, v]) => [t, v.n ? v.gs / v.n : 1.4]));
const teamStrength = Object.fromEntries([...conceded].map(([t, v]) => [t,
  { scored4: +(v.n ? v.gs / v.n : 1.4).toFixed(2), conceded4: +(v.n ? v.gc / v.n : 1.4).toFixed(2) }]));

// Fixtures for the next HORIZON events, per team per GW.
const HORIZON = 6; // his brief: "next 5-6 gameweeks"
const futureEvents = boot.events.filter((e) => e.id >= next.id).slice(0, HORIZON).map((e) => e.id);
const fxByGw = new Map();
for (const ev of futureEvents) {
  const fx = await j(`${API}/fixtures/?event=${ev}`);
  const m = new Map();
  for (const f of fx) {
    for (const [tid, opp, home] of [[f.team_h, f.team_a, true], [f.team_a, f.team_h, false]]) {
      const arr = m.get(tid) || [];
      arr.push({ opp, home });
      m.set(tid, arr);
    }
  }
  fxByGw.set(ev, m);
}
const teamsById = Object.fromEntries(boot.teams.map((t) => [t.id, t]));

// Per-player features + recent per-GW rows from element histories.
const pool = {};
let cursor = 0;
const elements = boot.elements;
async function worker() {
  while (cursor < elements.length) {
    const p = elements[cursor++];
    try {
      const s = await j(`${API}/element-summary/${p.id}/`);
      const perGw = new Map(); // gw -> {mins, pts, xgi} (double fixtures summed into one GW)
      for (const row of s.history) {
        const g = perGw.get(row.round) || { mins: 0, pts: 0, xgi: 0 };
        g.mins += row.minutes; g.pts += row.total_points;
        g.xgi += Number(row.expected_goal_involvements || 0);
        perGw.set(row.round, g);
      }
      const allGws = [...perGw.entries()].sort((a, b) => a[0] - b[0]);
      const recent = allGws.slice(-RECENT_GWS).map(([gw, g]) => ({ gw, pts: g.pts, mins: g.mins, xgi: +g.xgi.toFixed(2) }));
      const gws = allGws.slice(-TRAILING);
      const gw1row = s.history.find((r) => r.round === 1);
      const fixgw = Object.fromEntries(futureEvents.map((ev) => {
        const g = fxByGw.get(ev)?.get(p.team) || [];
        return [ev, g.length ? g.map((f) => `${teamsById[f.opp].short_name} ${f.home ? '(H)' : '(A)'}`).join(' + ') : 'BLANK'];
      }));
      const meta = { name: p.web_name, team: teamsById[p.team].short_name, pos: p.element_type,
        cost: p.now_cost / 10, status: p.status, news: p.news || '',
        selected_pct: Number(p.selected_by_percent),
        ep_next: p.ep_next === null ? null : Number(p.ep_next),
        chance_next: p.chance_of_playing_next_round,
        v1gw: gw1row && typeof gw1row.value === 'number' ? gw1row.value : null,
        recent, fixgw };
      if (gws.length < TRAILING) { pool[p.id] = { ...meta, rated: false, reason: 'cold start: fewer than 4 recent gameweeks' }; continue; }
      const mins = gws.reduce((z, [, g]) => z + g.mins, 0);
      if (mins < MIN_TRAILING_MINUTES) { pool[p.id] = { ...meta, rated: false, reason: 'cold start: under 180 recent minutes' }; continue; }
      const pts4 = gws.reduce((z, [, g]) => z + g.pts, 0) / TRAILING;
      const xgi4 = gws.reduce((z, [, g]) => z + g.xgi, 0) / TRAILING;
      const minshare4 = mins / (TRAILING * 90);
      const last2 = gws.slice(-2);
      const pts2 = last2.reduce((z, [, g]) => z + g.pts, 0) / 2;
      const xgi2 = last2.reduce((z, [, g]) => z + g.xgi, 0) / 2;
      const att = p.element_type >= 3 ? 1 : 0;
      const xpFor = (g) => {
        const home = g.reduce((z, f) => z + (f.home ? 1 : 0), 0) / g.length;
        const ogc = g.reduce((z, f) => z + (teamGc4.get(f.opp) ?? 1.4), 0) / g.length;
        const ogs = g.reduce((z, f) => z + (teamGs4.get(f.opp) ?? 1.4), 0) / g.length;
        return COEF.const + COEF.pts4 * pts4 + COEF.pts2 * pts2 + COEF.xgi4 * xgi4 + COEF.xgi2 * xgi2 +
          COEF.minshare4 * minshare4 + COEF.home * home +
          COEF.ogcAtt * ogc * att + COEF.ogcDef * ogc * (1 - att) +
          COEF.ogsAtt * ogs * att + COEF.ogsDef * ogs * (1 - att) +
          (POS_OFFSET[p.element_type] || 0);
      };
      const xpgw = {};
      for (const ev of futureEvents) {
        const g = fxByGw.get(ev)?.get(p.team) || [];
        if (!g.length) { xpgw[ev] = 0; continue; }
        xpgw[ev] = +(xpFor(g) * g.length).toFixed(2); // double GW ~ two matches, labeled approximation
      }
      pool[p.id] = { ...meta, rated: true,
        f: { pts4: +pts4.toFixed(2), pts2: +pts2.toFixed(2), xgi4: +xgi4.toFixed(2), xgi2: +xgi2.toFixed(2), minshare4: +minshare4.toFixed(2) },
        xp: xpgw[next.id] ?? 0, xpgw };
    } catch (e) {
      console.warn(`skipped ${p.web_name}: ${(e && e.name) || 'Error'}`);
    }
  }
}
await Promise.all(Array.from({ length: 12 }, worker));

await mkdir(OUT_DIR, { recursive: true });
await writeFile(new URL('pool.json', OUT_DIR), JSON.stringify({
  generated_at: new Date().toISOString(),
  model: 'docs/09 v1 coefficients (unchanged). xpgw holds trailing features constant across the horizon; doubles count as two matches; blanks are 0. Evidence fields (recent, form, consistency inputs) are raw official data, not projections.',
  model_version: 'v1',
  gameweek: next.id,
  deadline: next.deadline_time,
  horizon_gws: futureEvents,
  events: boot.events.filter((e) => e.id >= current.id - 1 && e.id <= next.id + HORIZON)
    .map((e) => ({ id: e.id, name: e.name, deadline: e.deadline_time, finished: e.finished, is_current: e.is_current, is_next: e.is_next })),
  chips: chipWindows,
  team_strength: teamStrength,
  source: `${API}/bootstrap-static, /element-summary, /fixtures (public)`,
  players: pool,
}, null, 2) + '\n');
const nRated = Object.values(pool).filter((x) => x.rated).length;
console.log(`v2 pool.json: ${Object.keys(pool).length} players (${nRated} rated) for GW${next.id}, horizon ${futureEvents.join('-')}`);
