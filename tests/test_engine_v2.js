/* Coverage + withholding tests for 12th-man/v2/engine.js (node).
   Run: node tests/test_engine_v2.js
   Scope: missing projections are distinct from real zeros; verdict/chip
   conclusions are withheld (not merely caveated) under partial coverage. */
const T = require('../12th-man/v2/engine.js');

let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; } else { fail++; console.log('FAIL:', name); } }

// synthetic pool: 4 players per position is enough for legal XIs
function mk(id, pos, xps, opts) {
  const o = Object.assign({ cost: 5.0, pos: pos, team: 'T' + (id % 7), recent: [], news: '', status: 'a', selected_pct: 1, fixgw: {}, ep_next: null }, opts || {});
  if (xps !== null && xps !== undefined) { o.rated = true; o.xpgw = {}; [9, 10, 11, 12, 13, 14].forEach((g, i) => o.xpgw[g] = xps); }
  else { o.rated = false; o.reason = 'cold start: under 180 recent minutes'; }
  return o;
}
const poolPlayers = {};
for (let i = 1; i <= 40; i++) poolPlayers[i] = mk(i, (i % 4) + 1, 3.0);
let poolArr = [];
function rebuild() { poolArr = Object.entries(poolPlayers).map(([id, p]) => ({ id: Number(id), ...p })); }
rebuild();

// squad: 15 rated players, legal shape
const ids = [1, 2, 5, 6, 7, 8, 9, 10, 13, 14, 15, 3, 4, 11, 12];
function squadFrom(list) {
  rebuild();
  return T.toEngine(list.map((id, i) => ({ id, slot: i + 1, selling: 5.0, pos: poolPlayers[id].pos, team: poolPlayers[id].team, cost: 5.0 })), poolPlayers);
}

// --- 1. coverage distinguishes missing projection from a real zero ---
poolPlayers[4] = mk(4, 1, 0.0); // rated, real zero projection (slot 14 -> bench)
let es = squadFrom(ids);
let cov = T.coverage(es, poolArr);
ok(cov.missing.length === 0, 'rated zero is not a missing projection');

// unrated with minutes -> missing + couldShift
poolPlayers[4] = mk(4, 1, null, { recent: [{ gw: 7, pts: 5, mins: 90, xgi: 0 }] });
es = squadFrom(ids);
cov = T.coverage(es, poolArr);
ok(cov.missing.length === 1 && cov.missing[0].id === 4, 'unrated player is missing');
ok(cov.couldShift === true, 'recent minutes => couldShift');

// unrated without minutes -> missing but no shift claim
poolPlayers[4] = mk(4, 1, null, { recent: [{ gw: 7, pts: 0, mins: 0, xgi: 0 }] });
es = squadFrom(ids);
cov = T.coverage(es, poolArr);
ok(cov.missing.length === 1 && cov.couldShift === false, 'no recent minutes => no shift claim');

// --- 2. assess wording: no "Best single fix" claim under missing coverage ---
let v = T.assess(es, poolArr, 9, 5.0);
ok(!/Best single fix/.test(v.why), 'assess never claims Best single fix with missing projection');
if (v.bestFix) ok(/rated-only/.test(v.why) || v.cls !== 'surgery', 'surgery why names rated-only fix');
poolPlayers[4] = mk(4, 1, 3.0);
es = squadFrom(ids);
v = T.assess(es, poolArr, 9, 5.0);
ok(!/rated-only/.test(v.why), 'full coverage: no rated-only qualifier');

// --- 3. BB withholding: conclusion removed, not just caveated ---
poolPlayers[4] = mk(4, 1, null, { recent: [{ gw: 7, pts: 5, mins: 90, xgi: 0 }] }); // slot 14 bench
es = squadFrom(ids);
const chipsLive = [{ name: 'bboost', state: 'live', expires: 19 }];
let cv = T.chipVerdicts(es, poolArr, chipsLive, 9, [9, 10, 11, 12, 13, 14], 5.0);
ok(cv.bboost.verdict === 'withheld', 'BB verdict withheld with unrated bench');
ok(!/weak week|playable|as strong as/.test(cv.bboost.why), 'BB withheld text carries no conclusion');
ok(!/higher by an unknown amount|are floors/.test(cv.bboost.why), 'BB text makes no bound claim');
ok(/partial estimate/.test(cv.bboost.why), 'BB text calls itself a partial estimate');

// rated bench -> normal verdict resumes
poolPlayers[4] = mk(4, 1, 3.0);
es = squadFrom(ids);
cv = T.chipVerdicts(es, poolArr, chipsLive, 9, [9, 10, 11, 12, 13, 14], 5.0);
ok(['candidate', 'borderline', 'hold'].includes(cv.bboost.verdict), 'BB normal verdict with full coverage');

// --- 4. sensitivity: giving the missing player a projection changes outputs ---
poolPlayers[4] = mk(4, 1, null, { recent: [{ gw: 7, pts: 5, mins: 90, xgi: 0 }] });
es = squadFrom(ids);
const before = T.assess(es, poolArr, 9, 5.0);
poolPlayers[4] = mk(4, 1, 9.0); // now rated high
es = squadFrom(ids);
const after = T.assess(es, poolArr, 9, 5.0);
ok(after.xiXp !== before.xiXp || JSON.stringify(after.bestFix) !== JSON.stringify(before.bestFix),
   'outputs are sensitive to a missing player gaining a projection (documents the defect coverage discloses)');

console.log(pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
