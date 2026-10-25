// Legality + sanity tests for 12th-man/engine.js. Run: node tests/test-12thman-engine.mjs
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const E = require('../12th-man/engine.js');

let failures = 0;
function ok(cond, name) { if (!cond) { failures++; console.error('FAIL:', name); } else console.log('ok:', name); }

// --- synthetic squad: 15 players, legal shape 2/5/5/3 ---
const GWS = [9, 10, 11, 12, 13];
function mkp(id, pos, team, cost, xp) {
  return { id, pos, team, cost, sell: cost, rated: true, name: 'P' + id,
           xpgw: Object.fromEntries(GWS.map((g) => [g, xp])) };
}
const squad = [
  mkp(1, 1, 'AAA', 5, 3), mkp(2, 1, 'BBB', 4, 2),
  mkp(3, 2, 'AAA', 5, 3), mkp(4, 2, 'BBB', 5, 3), mkp(5, 2, 'CCC', 4.5, 2.5), mkp(6, 2, 'DDD', 4, 2), mkp(7, 2, 'EEE', 4, 2),
  mkp(8, 3, 'AAA', 8, 4), mkp(9, 3, 'BBB', 7, 3.5), mkp(10, 3, 'CCC', 6, 3), mkp(11, 3, 'DDD', 5, 2), mkp(12, 3, 'EEE', 4.5, 1.5),
  mkp(13, 4, 'FFF', 10, 5), mkp(14, 4, 'GGG', 7, 3), mkp(15, 4, 'HHH', 6, 2.5),
];
const poolPlayers = {};
squad.forEach((p) => { poolPlayers[p.id] = { ...p, fixgw: {} }; });
// strong candidates the engine may chase (same teams to test club cap)
[101, 102, 103].forEach((id, i) => { poolPlayers[id] = { ...mkp(id, 3, 'AAA', 5 + i, 6 + i), fixgw: {} }; });
poolPlayers[110] = { ...mkp(110, 4, 'ZZZ', 12, 7), fixgw: {} }; // unaffordable on small bank
poolPlayers[111] = { ...mkp(111, 4, 'ZZZ', 5.5, 4), fixgw: {} }; // affordable upgrade over P15
const picks = squad.map((p) => ({ id: p.id, selling: p.sell }));

// --- bestXI: formation legality + captain doubling ---
const xi = E.bestXI(squad, 9);
ok(xi.xiIds.length === 11, 'bestXI returns 11 players');
ok(xi.captainId === 13, 'captain is highest-xP starter (P13)');
// best formation is 3-4-3: GK 3 + DEF 3,4,5 (8.5) + MID 8,9,10,11 (12.5) + FWD 13,14,15 (10.5) = 34.5; +captain 5 => 39.5
ok(Math.abs(xi.xp - 39.5) < 0.01, 'bestXI xp = base 34.5 + captain 5 = 39.5 (got ' + xi.xp + ')');

// --- club cap: squad already has 3x AAA; no 4th AAA allowed in ---
const roll = E.compare(picks, poolPlayers, { gws: GWS, bank: 100, fts: 5, chips: [] })[0];
ok(roll.total > 0, 'roll total positive');
const single = E.compare(picks, poolPlayers, { gws: GWS, bank: 100, fts: 1, chips: [] })[1];
const swappedTeams = single.moves.length ? single.moves.map((m) => m.inn) : [];
// cap-neutral swap (AAA out, AAA in) is legal; net AAA count must never exceed 3
const aaaOut = single.moves.filter((m) => ['P1','P3','P8'].includes(m.out)).length;
const aaaIn = single.moves.filter((m) => ['P101','P102','P103'].includes(m.inn)).length;
ok(3 + aaaIn - aaaOut <= 3, 'club cap: AAA count never exceeds 3 after swaps (in ' + aaaIn + ', out ' + aaaOut + ')');

// --- budget: 12.0 forward unreachable with bank 0.5 ---
const singlePoor = E.compare(picks, poolPlayers, { gws: GWS, bank: 0.5, fts: 1, chips: [] })[1];
ok(!singlePoor.moves.some((m) => m.inn === 'P110'), 'budget blocks unaffordable P110');

// --- FT accounting: 0 FTs => single-fix unavailable, aggressive uses hits only when gain > 4 ---
const noFT = E.compare(picks, poolPlayers, { gws: GWS, bank: 100, fts: 0, chips: [] });
ok(noFT[1].available === false, 'single-fix unavailable with 0 confirmed FTs');
const aggr = noFT[2];
ok(aggr.moves.filter((m) => m.gw === GWS[0]).every((m) => m.hit), 'with 0 FTs every GW' + GWS[0] + ' move is a hit');
ok(aggr.moves.filter((m) => !m.hit).every((m) => m.gw > GWS[0]), 'non-hit moves only appear once a new FT accrues');
ok(aggr.hits <= 2, 'hits capped at 2 (got ' + aggr.hits + ')');

// --- hits cost: total = raw horizon xp - 4*hits ---
ok(Math.abs(aggr.total - (aggr.perGw.reduce((z, r) => z + r.xp, 0) - aggr.hits * 4)) < 0.05, 'aggressive total nets out hit costs');

// --- wildcard: spent chip => unavailable ---
const wcSpent = E.compare(picks, poolPlayers, { gws: GWS, bank: 2, fts: 1, chips: [{ name: 'wildcard', event: 4 }] })[3];
ok(wcSpent.available === false && /spent/i.test(wcSpent.reasonUnavailable), 'spent wildcard shows unavailable');

// --- wildcard live: rebuild legal, within budget ---
const wc = E.compare(picks, poolPlayers, { gws: GWS, bank: 2, fts: 1, chips: [] })[3];
ok(wc.available === true, 'wildcard available when chip live');
const budget = squad.reduce((z, p) => z + p.sell, 0) + 2;
ok(wc.moves[0] && wc.moves[0].price <= budget + 1e-9, 'wildcard rebuild respects budget');

// --- unrated players: 0 xP, never hidden ---
const squad2 = squad.map((p) => ({ ...p }));
squad2[0] = { ...squad2[0], rated: false, xpgw: null };
const xi2 = E.bestXI(squad2, 9);
ok(xi2.unratedInXi >= 0 && typeof xi2.unratedInXi === 'number', 'unrated starters counted not hidden');

// --- NaN sell values (picks without selling_price) must not bypass the budget ---
const picksNaN = squad.map((p) => ({ id: p.id, selling: NaN }));
const singleNaN = E.compare(picksNaN, poolPlayers, { gws: GWS, bank: 0.5, fts: 1, chips: [] })[1];
ok(!singleNaN.moves.some((m) => m.inn === 'P110'), 'NaN selling price cannot bypass budget (no P110)');

console.log(failures ? failures + ' FAILURES' : 'ALL PASS');
process.exit(failures ? 1 : 0);
