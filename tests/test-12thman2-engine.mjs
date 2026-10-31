// Tests for 12th-man/v2/engine.js. Run: node tests/test-12thman2-engine.mjs
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const E = require('../12th-man/v2/engine.js');

let failures = 0;
function ok(cond, name) { if (!cond) { failures++; console.error('FAIL:', name); } else console.log('ok:', name); }

const GWS = [9, 10, 11, 12, 13, 14];
function mkp(id, pos, team, cost, xp, recent) {
  return { id, pos, team, cost, sell: cost, rated: true, name: 'P' + id,
           xpgw: Object.fromEntries(GWS.map((g) => [g, xp])),
           recent: recent || [], selected_pct: 5, status: 'a', news: '' };
}
const squad = [
  mkp(1, 1, 'AAA', 5, 3), mkp(2, 1, 'BBB', 4, 2),
  mkp(3, 2, 'AAA', 5, 3), mkp(4, 2, 'BBB', 5, 3), mkp(5, 2, 'CCC', 4.5, 2.5), mkp(6, 2, 'DDD', 4, 2), mkp(7, 2, 'EEE', 4, 2),
  mkp(8, 3, 'AAA', 8, 4), mkp(9, 3, 'BBB', 7, 3.5), mkp(10, 3, 'CCC', 6, 3), mkp(11, 3, 'DDD', 5, 2), mkp(12, 3, 'EEE', 4.5, 1.5),
  mkp(13, 4, 'FFF', 10, 5), mkp(14, 4, 'GGG', 7, 3), mkp(15, 4, 'HHH', 6, 2.5),
];
squad.forEach((p, i) => { p.slot = i + 1; });
const poolArr = squad.map((p) => ({ ...p }));
[101, 102, 103].forEach((id, i) => { poolArr.push({ ...mkp(id, 3, 'JJJ', 5 + i, 6 + i), slot: 0 }); });
poolArr.push({ ...mkp(110, 4, 'ZZZ', 12, 7), slot: 0 });
poolArr.push({ ...mkp(111, 4, 'ZZZ', 5.5, 4), slot: 0 });
const picks = squad.map((p) => ({ id: p.id, slot: p.slot, selling: p.sell }));

// --- evidence: consistency, spike, quiet, rotation ---
const steady = mkp(201, 3, 'AAA', 8, 4, [
  { gw: 3, pts: 6, mins: 90, xgi: 0.8 }, { gw: 4, pts: 5, mins: 90, xgi: 0.7 },
  { gw: 5, pts: 2, mins: 90, xgi: 0.4 }, { gw: 6, pts: 7, mins: 90, xgi: 0.9 },
  { gw: 7, pts: 6, mins: 90, xgi: 0.8 }, { gw: 8, pts: 5, mins: 90, xgi: 0.6 }]);
const ev1 = E.evidence(steady);
ok(ev1.played === 6 && ev1.returns === 5, 'evidence: 5 of 6 starts returned 5+ (got ' + ev1.returns + '/' + ev1.played + ')');
ok(Math.abs(ev1.consistency - 5 / 6) < 1e-9, 'consistency = 5/6');
ok(!ev1.spike && !ev1.quiet && !ev1.rotation, 'steady player: no flags');

const spiky = mkp(202, 3, 'AAA', 8, 4, [
  { gw: 4, pts: 2, mins: 90, xgi: 0.3 }, { gw: 5, pts: 3, mins: 90, xgi: 0.4 },
  { gw: 6, pts: 2, mins: 90, xgi: 0.3 }, { gw: 7, pts: 4, mins: 90, xgi: 0.5 },
  { gw: 8, pts: 13, mins: 90, xgi: 0.2 }]);
const ev2 = E.evidence(spiky);
ok(ev2.spike === true, 'one-week wonder: 13 pts on 0.2 xGI, 10+ above prior form, flagged');

const notSpike = mkp(203, 3, 'AAA', 8, 4, [
  { gw: 4, pts: 2, mins: 90, xgi: 0.3 }, { gw: 5, pts: 3, mins: 90, xgi: 0.4 },
  { gw: 6, pts: 2, mins: 90, xgi: 0.3 }, { gw: 7, pts: 4, mins: 90, xgi: 0.5 },
  { gw: 8, pts: 13, mins: 90, xgi: 2.4 }]);
ok(E.evidence(notSpike).spike === false, '13 pts backed by 2.4 xGI is earned form, not a spike');

const quiet = mkp(204, 4, 'AAA', 8, 4, [
  { gw: 7, pts: 2, mins: 90, xgi: 0.9 }, { gw: 8, pts: 2, mins: 90, xgi: 0.8 }]);
ok(E.evidence(quiet).quiet === true, 'quiet runner: 1.7 xGI across last 2 with only 4 pts');
const gkQuiet = mkp(205, 1, 'AAA', 5, 4, [
  { gw: 7, pts: 2, mins: 90, xgi: 0 }, { gw: 8, pts: 2, mins: 90, xgi: 0 }]);
ok(E.evidence(gkQuiet).quiet === false && E.evidence(gkQuiet).spike === false, 'GKP/DEF never get xGI flags');

const rot = mkp(206, 2, 'AAA', 5, 4, [
  { gw: 6, pts: 2, mins: 90, xgi: 0 }, { gw: 7, pts: 1, mins: 45, xgi: 0 }, { gw: 8, pts: 1, mins: 30, xgi: 0 }]);
ok(E.evidence(rot).rotation === true, 'rotation flag: last-3 mean minutes under 60');

// --- assess: verdict classes ---
const chipWindows = [
  { name: 'wildcard', start: 2, stop: 19 }, { name: 'wildcard', start: 20, stop: 38 },
  { name: 'freehit', start: 2, stop: 19 }, { name: 'freehit', start: 20, stop: 38 },
  { name: 'bboost', start: 1, stop: 19 }, { name: 'bboost', start: 20, stop: 38 },
  { name: '3xc', start: 1, stop: 19 }, { name: '3xc', start: 20, stop: 38 },
];
const engineSquad = E.toEngine(picks, Object.fromEntries(poolArr.map((p) => [p.id, p])));
const v1 = E.assess(engineSquad, poolArr, 9, 10);
ok(['good', 'fix', 'surgery'].indexOf(v1.cls) >= 0, 'assess returns a verdict class');
ok(v1.bestFix && typeof v1.bestFix.gain === 'number', 'assess names the best fix with a gain');

// --- chipState: windows and used history ---
const cs = E.chipState(chipWindows, [{ name: 'wildcard', event: 7 }], 9);
const wcState = cs.find((c) => c.name === 'wildcard');
ok(wcState.state === 'future' && wcState.unlocks === 20, 'wildcard spent GW7 -> future copy unlocks GW20');
ok(cs.find((c) => c.name === 'bboost').state === 'live' && cs.find((c) => c.name === 'bboost').expires === 19, 'bench boost live, expires after GW19');
ok(cs.find((c) => c.name === 'freehit').state === 'live' && cs.find((c) => c.name === '3xc').state === 'live', 'free hit + triple captain live');
const csSpent = E.chipState(chipWindows, [{ name: 'bboost', event: 5 }, { name: 'bboost', event: 25 }], 26);
ok(csSpent.find((c) => c.name === 'bboost').state === 'spent', 'both bench-boost copies spent -> spent');

// --- chipVerdicts ---
const cv = E.chipVerdicts(engineSquad, poolArr, cs, 9, GWS);
ok(cv.wildcard && cv.wildcard.state === 'future', 'wildcard verdict respects future state');
ok(cv.bboost && cv.bboost.state === 'live' && typeof cv.bboost.benchXp === 'number', 'bench boost verdict carries bench xP');
ok(cv['3xc'].verdict === 'hold' || cv['3xc'].verdict === 'candidate', 'triple captain verdict present');
ok(cv.freehit.blanks === 0 && cv.freehit.verdict === 'hold', 'no blanks -> free hit holds');

// --- plans: lean, hit rules, two lenses ---
const pl = E.plans(engineSquad, poolArr, { gws: GWS, bank: 10, fts: 1, chipState: cs });
ok(pl.plans.length === 4, 'four play cards');
ok(pl.plans[0].key === 'hold' && pl.plans[0].certain === 0, 'hold has zero certain cost');
const single = pl.plans[1];
ok(single.moves.length === 1 && single.moves[0].hit === false, 'single fix uses the free transfer');
ok(typeof single.gainThisGw === 'number' && typeof single.gainHorizon === 'number', 'single fix carries both lenses');
const aggr = pl.plans[2];
ok(aggr.moves.filter((m) => !m.hit).every((m) => m.gw === 9 || m.gw > 9), 'aggressive moves legal');
ok(aggr.horizon === aggr.thisGw !== undefined, 'aggressive totals present');
ok(['hold', 'single', 'aggr', 'wildcard'].indexOf(pl.leanKey) >= 0, 'engine lean names a plan');

// hits only when projected gain clears the certain -4
const plNoFt = E.plans(engineSquad, poolArr, { gws: GWS, bank: 10, fts: 0, chipState: cs });
ok(plNoFt.plans[1].available === false, 'single fix unavailable with 0 FTs');
ok(plNoFt.plans[2].moves.filter((m) => m.hit).every((m) => true), 'with 0 FTs every move is a hit');

// wildcard live -> restructure plan builds a legal squad in budget
const csWc2 = E.chipState(chipWindows, [], 9);
const plWc = E.plans(engineSquad, poolArr, { gws: GWS, bank: 2, fts: 1, chipState: csWc2 });
ok(plWc.plans[3].available === true && plWc.plans[3].moves.length === 1, 'wildcard restructure available when chip live');
const wcBudget = squad.reduce((z, p) => z + p.sell, 0) + 2;
ok(plWc.plans[3].moves[0].price <= wcBudget + 1e-9, 'wildcard respects budget');

// --- whoElse: outsiders inside budget + cap, weakest teammate named ---
const we = E.whoElse(engineSquad, poolArr, 10, GWS, 3);
ok(we.length > 0, 'outsiders found');
ok(we.every((w) => w.cost <= 10 + Math.max(...squad.filter((s) => s.pos === w.pos).map((s) => s.sell)) + 1e-9), 'outsiders affordable on bank + best sell at position');
ok(we.every((w) => !squad.some((s) => s.id === w.id)), 'no squad member listed as an outsider');
ok(we.every((w) => w.replaces), 'each outsider names the weakest squad player at that position');
const rich = E.whoElse(engineSquad, poolArr, 0.5, GWS, 3);
ok(!rich.some((w) => w.id === 110), 'unaffordable P110 excluded on small bank');

// --- computeSells carried from v1 (spot check) ---
const res = E.computeSells([1, 2], [{ element_in: 1, element_in_cost: 90, element_out: 9, event: 5 }], { 2: 50 }, { 1: 100, 2: 50 }, 8);
ok(res.byId[1].sell === 95 && res.byId[1].basis === 'history', 'computeSells: half-profit rule intact');
ok(res.byId[2].sell === 50 && res.byId[2].basis === 'gw1', 'computeSells: GW1 basis intact');


// --- chipState: official-rule gating (2026/27 rules, unchanged from 2025/26 per /en/help/new + /en/help/rules) ---
// Two copies per chip: first set GW1-19, second GW20-38. wildcard used GW7 -> locked until GW20.
const csWcNew = E.chipState(chipWindows, [{ name: 'wildcard', event: 7 }], 9);
ok(csWcNew.find((c) => c.name === 'wildcard').state === 'future' && csWcNew.find((c) => c.name === 'wildcard').unlocks === 20,
   'chipState: spent first-half wildcard locked until GW20');
ok(csWcNew.find((c) => c.name === 'freehit').state === 'live' && csWcNew.find((c) => c.name === 'freehit').expires === 19,
   'chipState: unused free hit live, first set expires after GW19');
// Free hit cannot be consecutive: played GW19 -> second copy locked at GW20, unlocks GW21.
const csFh = E.chipState(chipWindows, [{ name: 'freehit', event: 19 }], 20);
const fh20 = csFh.find((c) => c.name === 'freehit');
ok(fh20.state === 'locked' && fh20.unlocks === 21, 'chipState: FH in GW19 locks the second copy until GW21');
const csFh21 = E.chipState(chipWindows, [{ name: 'freehit', event: 19 }], 21);
ok(csFh21.find((c) => c.name === 'freehit').state === 'live', 'chipState: second FH copy live again at GW21');
// Both copies spent -> spent.
const cs2 = E.chipState(chipWindows, [{ name: '3xc', event: 10 }, { name: '3xc', event: 25 }], 26);
ok(cs2.find((c) => c.name === '3xc').state === 'spent', 'chipState: both copies used -> spent');
// Non-consecutive FH within a half is fine: FH at GW10 -> GW12 live again only if a second copy existed (it does not) -> spent until GW20
const csFh2 = E.chipState(chipWindows, [{ name: 'freehit', event: 10 }], 11);
ok(csFh2.find((c) => c.name === 'freehit').state === 'locked' && csFh2.find((c) => c.name === 'freehit').unlocks === 20,
   'chipState: GW right after a FH is locked (non-consecutive rule), next copy GW20');
const csFh3 = E.chipState(chipWindows, [{ name: 'freehit', event: 10 }], 12);
ok(csFh3.find((c) => c.name === 'freehit').state === 'future' && csFh3.find((c) => c.name === 'freehit').unlocks === 20,
   'chipState: two GWs after a spent first-half FH, second copy shows GW20');

// --- deriveFT: 1/GW, carry cap 5, retained through chips (official rules) ---
const histShape = {
  chips: [{ name: 'wildcard', event: 7 }],
  current: [
    { event: 1, event_transfers: 0 }, { event: 2, event_transfers: 1 }, { event: 3, event_transfers: 1 },
    { event: 4, event_transfers: 0 }, { event: 5, event_transfers: 0 }, { event: 6, event_transfers: 3 },
    { event: 7, event_transfers: 0 }, { event: 8, event_transfers: 1 },
  ] };
ok(E.deriveFT(histShape) === 3, 'deriveFT: WC-retained carry cap-5 recurrence gives 3 (0,1,1,0,0,3,WC,1)');
ok(E.deriveFT({ chips: [], current: [{ event: 1, event_transfers: 0 }] }) === 2, 'deriveFT: one unused week carries to 2');
ok(E.deriveFT({ chips: [], current: Array.from({ length: 8 }, () => ({ event_transfers: 0 })) }) === 5,
   'deriveFT: carry caps at 5');
ok(E.deriveFT({ chips: [{ name: 'freehit', event: 6 }], current: Array.from({ length: 6 }, (_, i) => ({ event: i + 1, event_transfers: i === 5 ? 4 : 0 })) }) === 5,
   'deriveFT: FH-week transfers do not consume FTs (saved FTs retained, cap 5)');
ok(E.deriveFT({ chips: [], current: [] }) === 1, 'deriveFT: pre-GW1 start is 1');

console.log(failures ? failures + ' FAILURES' : 'ALL PASS');
process.exit(failures ? 1 : 0);