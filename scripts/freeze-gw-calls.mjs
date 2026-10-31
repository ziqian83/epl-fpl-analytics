// Freeze the v2 engine's calls for a gameweek BEFORE its deadline (FPL accountability artifact).
// Usage (run from repo root):
//   FPL_ENTRY_ID=<id> node scripts/freeze-gw-calls.mjs            # fetch live, freeze current GW
//   node scripts/freeze-gw-calls.mjs --snapshot-dir /path          # reuse saved API snapshots
// The entry ID is only ever read from the environment or snapshot files; it is never written
// into the artifact. Output: 12th-man/v2/data/frozen/gwNN.json
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const require = createRequire(import.meta.url);
const E = require('../12th-man/v2/engine.js');
const pool = JSON.parse(readFileSync('./12th-man/v2/data/pool.json', 'utf8'));
const poolHash = createHash('sha256').update(readFileSync('./12th-man/v2/data/pool.json')).digest('hex').slice(0, 16);
const engineHash = createHash('sha256').update(readFileSync('./12th-man/v2/engine.js')).digest('hex').slice(0, 16);

const snapIdx = process.argv.indexOf('--snapshot-dir');
let picks, hist, transfers;
if (snapIdx >= 0) {
  const dir = process.argv[snapIdx + 1];
  picks = JSON.parse(readFileSync(dir + '/picks8.json', 'utf8'));
  hist = JSON.parse(readFileSync(dir + '/hist.json', 'utf8'));
  transfers = JSON.parse(readFileSync(dir + '/transfers.json', 'utf8'));
} else {
  const id = process.env.FPL_ENTRY_ID;
  if (!id) { console.error('set FPL_ENTRY_ID or pass --snapshot-dir'); process.exit(1); }
  const get = async u => (await fetch(u)).json();
  const gw = pool.gameweek - 1; // last locked gameweek: pre-deadline the current GW's picks are not visible
  picks = await get(`https://fantasy.premierleague.com/api/entry/${id}/event/${gw}/picks/`);
  hist = await get(`https://fantasy.premierleague.com/api/entry/${id}/history/`);
  transfers = await get(`https://fantasy.premierleague.com/api/entry/${id}/transfers/`);
}

const poolArr = Object.entries(pool.players).map(([id, p]) => { p.id = Number(id); return p; });
const sells = E.computeSells(picks.picks.map(p => p.element), transfers,
  Object.fromEntries(poolArr.filter(p => typeof p.v1gw === 'number').map(p => [p.id, p.v1gw])),
  Object.fromEntries(poolArr.map(p => [p.id, Math.round(p.cost * 10)])), pool.gameweek - 1);
const squadPicks = picks.picks.map(pk => {
  const pl = pool.players[pk.element];
  const cs = sells.byId[pk.element];
  return { id: pk.element, slot: pk.position, captain: pk.is_captain, vice: pk.is_vice_captain,
           rated: !!(pl && pl.rated), p: pl || null,
           selling: pk.selling_price != null ? pk.selling_price / 10 : (cs && cs.sell != null ? cs.sell / 10 : null) };
});
const es = E.toEngine(squadPicks.map(x => ({ id: x.id, slot: x.slot, selling: x.selling, pos: x.p ? x.p.pos : null, team: x.p ? x.p.team : null, cost: x.p ? x.p.cost : null })), pool.players);
const ft = E.deriveFT(hist);
const bank = picks.entry_history.bank / 10;
const chipWindows = [
  { name: 'wildcard', start: 2, stop: 19 }, { name: 'wildcard', start: 20, stop: 38 },
  { name: 'freehit', start: 2, stop: 19 }, { name: 'freehit', start: 20, stop: 38 },
  { name: 'bboost', start: 1, stop: 19 }, { name: 'bboost', start: 20, stop: 38 },
  { name: '3xc', start: 1, stop: 19 }, { name: '3xc', start: 20, stop: 38 },
];
const chipState = E.chipState(chipWindows, hist.chips, pool.gameweek);
const verdict = E.assess(es, poolArr, pool.gameweek, bank);
const chips = E.chipVerdicts(es, poolArr, chipState, pool.gameweek, pool.horizon_gws, bank);
const plans = E.plans(es, poolArr, { gws: pool.horizon_gws, bank, fts: ft, chipState });
const frozen = {
  kind: 'engine diagnostic snapshot: predictions frozen before the GW deadline. NOT the user\'s confirmed plan - the user owns every decision. Squad and bank/FT inputs are derived from the last locked gameweek and are UNCONFIRMED BY THE USER.',
  frozen_at: new Date().toISOString(),
  gameweek: pool.gameweek,
  deadline_utc: '2026-10-31T11:00:00Z',
  pool_sha256_16: poolHash, engine_sha256_16: engineHash,
  model: pool.model, horizon: pool.horizon_gws,
  inputs: {
    squad_asof: 'locked GW' + (pool.gameweek - 1) + ' (the upcoming GW\'s picks are not visible before the deadline)',
    ft_derived: ft, bank_at_lock: bank,
    confirmed_by_user: false,
    note: 'bank/FT are test inputs derived from locked-GW history; the user has not confirmed his current bank, free transfers, or lineup. Any engine interactions during testing do not establish his live state.',
    chips_used: hist.chips.map(c => ({ name: c.name, event: c.event }))
  },
  squad: squadPicks.map(x => ({ name: x.p ? x.p.name : '#' + x.id, slot: x.slot, captain: x.captain })),
  calls: {
    verdict: { cls: verdict.cls, label: verdict.label, why: verdict.why, xiXp: verdict.xiXp,
               bestFix: verdict.bestFix, flagged: verdict.flagged },
    chips: JSON.parse(JSON.stringify(chips)),
    lean: plans.leanKey, leanWhy: plans.leanWhy,
    plans: plans.plans.map(p => ({ key: p.key, title: p.title, net: p.net, gwNet: p.gwNet, cost: p.cost }))
  },
  fh_baseline: 'free-hit uplift is measured against the engine\'s best feasible XI under formation, bench budget and club-cap constraints (' + verdict.xiXp + ' xP), NOT against the user\'s picked XI, which is unknowable before the deadline.',
  scoring_rule: 'After GW9 completes: fetch actual points per player from the official API. Score the PRE-FROZEN choices only - no hindsight re-selection of the XI or of transfer targets: (a) bestFix realized edge (Tavernier actual - Cherki actual), (b) frozen XI xP 45.6 vs the realized total of the frozen best XI, (c) FH uplift claim (frozen fhXiXp vs the frozen best-affordable-XI\'s actual points), (d) every chip verdict against realized outcomes. The hindsight oracle best-XI is reported separately as a diagnostic only, never as the benchmark the frozen calls are judged against. Publish the comparison alongside this file.'
};
const out = './12th-man/v2/data/frozen/gw' + String(pool.gameweek).padStart(2, '0') + '.json';
writeFileSync(out, JSON.stringify(frozen, null, 2));
console.log('frozen ->', out, '| verdict:', verdict.cls, '| bestFix:', JSON.stringify(verdict.bestFix), '| fh uplift:', chips.freehit && chips.freehit.uplift, '| lean:', plans.leanKey);
