// The 12th Man - daily pool refresh (fresh build, 25 Oct 2026).
// Writes 12th-man/data/pool.json: GENERIC per-player expected points for the next
// gameweek. No team IDs, no squads, no personal state - publishable by construction.
// Model: docs/09_12thman_model.md (OLS coefficients fitted on 2021-22..2024-25,
// validated on rolling held-out seasons). Fresh code; consumes only public FPL API.

import { mkdir, writeFile } from 'node:fs/promises';

const API = 'https://fantasy.premierleague.com/api';
const OUT_DIR = new URL('../12th-man/data/', import.meta.url);
const TRAILING = 4;
const MIN_TRAILING_MINUTES = 180;

// docs/09 coefficients (2025-26 holdout fit); position offsets relative to MID.
const COEF = { const: 0.478, pts4: 0.241, xgi4: 1.118, minshare4: 1.44, oppstr: 0.005 };
const POS_OFFSET = { 1: 0.135, 2: -0.353, 3: 0.0, 4: 0.165 }; // GKP DEF MID FWD

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

// Team defensive strength entering GW `next`: mean goals conceded per match over
// the TRAILING completed gameweeks, from finished-fixture scores.
const completedIds = boot.events.filter((e) => e.finished).map((e) => e.id).slice(-TRAILING);
const conceded = new Map(); // team id -> {gc, n}
for (const ev of completedIds) {
  const fx = await j(`${API}/fixtures/?event=${ev}`);
  for (const f of fx) {
    if (!f.finished) continue;
    const h = conceded.get(f.team_h) || { gc: 0, n: 0 };
    h.gc += f.team_a_score; h.n += 1; conceded.set(f.team_h, h);
    const a = conceded.get(f.team_a) || { gc: 0, n: 0 };
    a.gc += f.team_h_score; a.n += 1; conceded.set(f.team_a, a);
  }
}
const teamGc4 = new Map([...conceded].map(([t, v]) => [t, v.n ? v.gc / v.n : 1.4]));

// Next-GW fixtures: per team, opponent strength (avg over double fixtures) + label.
const nextFx = await j(`${API}/fixtures/?event=${next.id}`);
const byTeam = new Map();
for (const f of nextFx) {
  for (const [tid, opp, home] of [[f.team_h, f.team_a, true], [f.team_a, f.team_h, false]]) {
    const arr = byTeam.get(tid) || [];
    arr.push({ opp, home });
    byTeam.set(tid, arr);
  }
}
const teamsById = Object.fromEntries(boot.teams.map((t) => [t.id, t]));

// Trailing per-player features from element histories (last TRAILING entries,
// which are per-gameweek rows; doubles are separate rows and summed per GW first).
const pool = {};
let cursor = 0;
const elements = boot.elements;
async function worker() {
  while (cursor < elements.length) {
    const p = elements[cursor++];
    try {
      const s = await j(`${API}/element-summary/${p.id}/`);
      const perGw = new Map(); // gw -> {mins, pts, xgi}
      for (const row of s.history) {
        const g = perGw.get(row.round) || { mins: 0, pts: 0, xgi: 0 };
        g.mins += row.minutes; g.pts += row.total_points;
        g.xgi += Number(row.expected_goal_involvements || 0);
        perGw.set(row.round, g);
      }
      const gws = [...perGw.entries()].sort((a, b) => a[0] - b[0]).slice(-TRAILING);
      if (gws.length < TRAILING) continue;
      const mins = gws.reduce((z, [, g]) => z + g.mins, 0);
      if (mins < MIN_TRAILING_MINUTES) continue;
      const pts4 = gws.reduce((z, [, g]) => z + g.pts, 0) / TRAILING;
      const xgi4 = gws.reduce((z, [, g]) => z + g.xgi, 0) / TRAILING;
      const minshare4 = mins / (TRAILING * 90);
      const fx = byTeam.get(p.team) || [];
      if (!fx.length) continue; // blank gameweek: no fixture, no xP
      const oppStr = fx.reduce((z, f) => z + (teamGc4.get(f.opp) ?? 1.4), 0) / fx.length;
      const xp = COEF.const + COEF.pts4 * pts4 + COEF.xgi4 * xgi4 +
        COEF.minshare4 * minshare4 + COEF.oppstr * oppStr + (POS_OFFSET[p.element_type] || 0);
      pool[p.id] = {
        name: p.web_name, team: teamsById[p.team].short_name, pos: p.element_type,
        cost: p.now_cost / 10, status: p.status, news: p.news || '',
        selected_pct: Number(p.selected_by_percent),
        f: { pts4: +pts4.toFixed(2), xgi4: +xgi4.toFixed(2), minshare4: +minshare4.toFixed(2), oppstr: +oppStr.toFixed(2) },
        fixtures: fx.map((f) => `${teamsById[f.opp].short_name} ${f.home ? '(H)' : '(A)'}`),
        xp: +xp.toFixed(2),
      };
    } catch (e) {
      console.warn(`skipped ${p.web_name}: ${e.message}`);
    }
  }
}
await Promise.all(Array.from({ length: 12 }, worker));

await mkdir(OUT_DIR, { recursive: true });
await writeFile(new URL('pool.json', OUT_DIR), JSON.stringify({
  generated_at: new Date().toISOString(),
  model: 'docs/09_12thman_model.md v0 - OLS on trailing-4GW features; validated rolling holdouts; ranking tool, not point-precise',
  gameweek: next.id,
  deadline: next.deadline_time,
  source: `${API}/bootstrap-static, /element-summary, /fixtures (public)`,
  players: pool,
}, null, 2) + '\n');
console.log(`pool.json: ${Object.keys(pool).length} players for GW${next.id}`);
