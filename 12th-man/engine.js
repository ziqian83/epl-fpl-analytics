/* The 12th Man - horizon strategy engine (fresh build, 25 Oct 2026; v1 sells 26 Oct 2026).
   Compares genuinely different transfer postures across the fixture horizon.
   Pure functions over pool.json + the user's squad; no DOM, no fetches, so the
   same file runs in the browser (window.T12Engine) and under node (tests).
   Everything it returns is a WEAK, UNVALIDATED estimate: pool xP comes from a
   model whose rolling holdouts beat a naive baseline by ~1pp pairwise ordering.
   Known simplifications (each labeled in the UI):
   - prices frozen across the horizon; a bought player sells at cost
   - trailing features held constant (form decay unmodeled)
   - transfers settle at the start of each gameweek
   - unrated (cold-start) players contribute 0 xP and are counted, never hidden */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.T12Engine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  var POSN = { 1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD' };
  var SQUAD_SHAPE = { 1: 2, 2: 5, 3: 5, 4: 3 };
  var CLUB_CAP = 3;
  var FT_MAX = 5;
  var HIT_COST = 4;
  // legal XI formations as [DEF, MID, FWD]
  var FORMATIONS = [[3, 4, 3], [3, 5, 2], [4, 3, 3], [4, 4, 2], [4, 5, 1], [5, 2, 3], [5, 3, 2], [5, 4, 1]];

  function xpOf(player, gw) {
    if (!player || !player.rated || !player.xpgw) return 0;
    return player.xpgw[gw] || 0;
  }

  // Best XI + captain for one GW. Returns { xp, xiIds, captainId, unratedInXi }.
  function bestXI(squadPlayers, gw) {
    var best = null;
    for (var f = 0; f < FORMATIONS.length; f++) {
      var need = { 1: 1, 2: FORMATIONS[f][0], 3: FORMATIONS[f][1], 4: FORMATIONS[f][2] };
      var xi = [];
      var ok = true;
      for (var pos = 1; pos <= 4; pos++) {
        var inPos = squadPlayers.filter(function (p) { return p.pos === pos; })
          .sort(function (a, b) { return xpOf(b, gw) - xpOf(a, gw); });
        if (inPos.length < need[pos]) { ok = false; break; }
        xi = xi.concat(inPos.slice(0, need[pos]));
      }
      if (!ok) continue;
      var base = xi.reduce(function (z, p) { return z + xpOf(p, gw); }, 0);
      if (!best || base > best.base) best = { base: base, xi: xi };
    }
    if (!best) return { xp: 0, xiIds: [], captainId: null, unratedInXi: 0 };
    var cap = best.xi.slice().sort(function (a, b) { return xpOf(b, gw) - xpOf(a, gw); })[0];
    var unr = best.xi.filter(function (p) { return !p.rated; }).length;
    return {
      xp: +(best.base + xpOf(cap, gw)).toFixed(2),
      xiIds: best.xi.map(function (p) { return p.id; }),
      captainId: cap ? cap.id : null,
      unratedInXi: unr,
    };
  }

  function clubCounts(players) {
    var c = {};
    players.forEach(function (p) { c[p.team] = (c[p.team] || 0) + 1; });
    return c;
  }

  function legalClubCap(players) {
    var c = clubCounts(players);
    return Object.keys(c).every(function (t) { return c[t] <= CLUB_CAP; });
  }

  // Candidate pool: top N rated per position by horizon xP, plus cheapest rated per position.
  function candidates(poolPlayers, gws, perPos) {
    var horizon = function (p) { return gws.reduce(function (z, g) { return z + xpOf(p, g); }, 0); };
    var out = [];
    for (var pos = 1; pos <= 4; pos++) {
      var inPos = poolPlayers.filter(function (p) { return p.pos === pos && p.rated; });
      var byXp = inPos.slice().sort(function (a, b) { return horizon(b) - horizon(a); }).slice(0, perPos);
      var cheap = inPos.slice().sort(function (a, b) { return a.cost - b.cost; }).slice(0, 2);
      var seen = {};
      byXp.concat(cheap).forEach(function (p) { if (!seen[p.id]) { seen[p.id] = 1; out.push(p); } });
    }
    return out;
  }

  // One swap on a squad of engine players. Engine player: {id, pos, team, cost, sell, rated, xpgw, name}.
  function applySwap(squad, outId, inPlayer) {
    return squad.map(function (p) {
      if (p.id !== outId) return p;
      return { id: inPlayer.id, pos: inPlayer.pos, team: inPlayer.team, cost: inPlayer.cost,
               sell: inPlayer.cost, rated: inPlayer.rated, xpgw: inPlayer.xpgw, name: inPlayer.name };
    });
  }

  function horizonXp(squad, gws) {
    var perGw = gws.map(function (gw) { return bestXI(squad, gw); });
    return { total: +perGw.reduce(function (z, r) { return z + r.xp; }, 0).toFixed(2), perGw: perGw };
  }

  // Best legal+affordable single swap for the remaining horizon. Returns null when none beats 0.
  function bestSwap(squad, cands, bank, gws) {
    var before = horizonXp(squad, gws).total;
    var best = null;
    for (var o = 0; o < squad.length; o++) {
      var out = squad[o];
      for (var i = 0; i < cands.length; i++) {
        var inn = cands[i];
        if (inn.pos !== out.pos || inn.id === out.id) continue;
        if (squad.some(function (p) { return p.id === inn.id; })) continue;
        var price = inn.cost - out.sell;
        if (price > bank + 1e-9) continue;
        var next = applySwap(squad, out.id, inn);
        if (!legalClubCap(next)) continue;
        var gain = horizonXp(next, gws).total - before;
        if (!best || gain > best.gain) best = { out: out, inn: inn, gain: +gain.toFixed(2), price: +price.toFixed(2) };
      }
    }
    return best && best.gain > 0 ? best : null;
  }

  function toEngine(squadPicks, poolPlayers) {
    return squadPicks.map(function (pk) {
      var pl = poolPlayers[pk.id] || poolPlayers[String(pk.id)] || null;
      var sellKnown = typeof pk.selling === 'number' && Number.isFinite(pk.selling);
      return { id: pk.id, pos: pl ? pl.pos : pk.pos, team: pl ? pl.team : pk.team,
               cost: pl ? pl.cost : pk.cost, sell: sellKnown ? pk.selling : (pl ? pl.cost : 0), sellAssumed: !sellKnown,
               rated: !!(pl && pl.rated), xpgw: pl ? pl.xpgw : null, name: pl ? pl.name : ('Player #' + pk.id) };
    });
  }

  /* Strategies. Each returns { key, label, available, moves[], hits, total, perGw[], notes[], unknowns[] }.
     moves: { gw, out, inn, price, hit:bool }. */

  function stratRoll(squad, gws) {
    var h = horizonXp(squad, gws);
    var unrated = squad.filter(function (p) { return !p.rated; }).length;
    return { key: 'roll', label: 'Hold and roll the transfers', available: true, moves: [], hits: 0,
      total: h.total, perGw: h.perGw,
      notes: ['Free transfers carry (max ' + FT_MAX + '): every unspent transfer is another option next week.',
              'Zero certain cost. You keep all future flexibility.'],
      unknowns: unrated ? [unrated + ' squad player(s) unrated - their real minutes are invisible to the model'] : [] };
  }

  function stratSingleFix(squad, cands, bank, fts, gws) {
    if (fts < 1) return { key: 'single', label: 'One targeted fix, then roll', available: false,
      reasonUnavailable: 'Needs 1 free transfer; you have confirmed 0.', moves: [], hits: 0, total: null, perGw: [], notes: [], unknowns: [] };
    var sw = bestSwap(squad, cands, bank, gws);
    if (!sw) return { key: 'single', label: 'One targeted fix, then roll', available: true, moves: [], hits: 0,
      total: horizonXp(squad, gws).total, perGw: horizonXp(squad, gws).perGw,
      notes: ['No single legal swap improves the horizon projection - this posture collapses into Hold.'], unknowns: [] };
    var next = applySwap(squad, sw.out.id, sw.inn);
    var h = horizonXp(next, gws);
    return { key: 'single', label: 'One targeted fix, then roll', available: true,
      moves: [{ gw: gws[0], out: sw.out.name, inn: sw.inn.name, price: sw.price, hit: false }],
      hits: 0, total: h.total, perGw: h.perGw,
      notes: ['One move now (' + sw.out.name + ' -> ' + sw.inn.name + '), then hold. Keeps transfers in hand from GW' + (gws[0] + 1) + '.',
              'Horizon gain over holding: +' + sw.gain + ' xP (weak, uncalibrated).'], unknowns: [] };
  }

  function stratAggressive(squad, cands, bank, fts, gws, maxHits) {
    var cur = squad.slice();
    var cash = bank, free = fts, hits = 0, moves = [];
    for (var g = 0; g < gws.length; g++) {
      var remaining = gws.slice(g);
      while (true) {
        var sw = bestSwap(cur, cands, cash, remaining);
        if (!sw) break;
        var isHit = free < 1;
        if (isHit && hits >= maxHits) break;
        if (isHit && sw.gain <= HIT_COST) break; // hit must clear its certain cost in weak xP
        cur = applySwap(cur, sw.out.id, sw.inn);
        cash -= sw.price;
        moves.push({ gw: remaining[0], out: sw.out.name, inn: sw.inn.name, price: sw.price, hit: isHit });
        if (isHit) hits++; else free--;
      }
      free = Math.min(free + 1, FT_MAX);
    }
    var h = horizonXp(cur, gws);
    return { key: 'aggr', label: 'Aggressive restructure (hits allowed)', available: true,
      moves: moves, hits: hits, total: +(h.total - hits * HIT_COST).toFixed(2), perGw: h.perGw,
      notes: [hits > 0
        ? moves.length + ' move(s) across the horizon, ' + hits + ' on a hit (certain -' + (hits * HIT_COST) + ').'
        : (moves.length
          ? 'No hit taken: none cleared the >4pt gain bar, so this policy converges on the same move(s) as the targeted fix. Shown as its own policy, not presented as a different plan.'
          : 'No swap sequence beat its certain costs - this posture collapses into Hold.'),
        'A hit is only taken when the weak projection clears the certain -4; that margin is not calibrated.'],
      unknowns: ['Prices are frozen in the model - real price changes alter what is affordable'] };
  }

  function stratWildcard(squad, cands, poolPlayers, bank, chips, gws) {
    var wcUsed = (chips || []).some(function (c) { return c.name === 'wildcard'; });
    if (wcUsed) return { key: 'wildcard', label: 'Wildcard restructure', available: false,
      reasonUnavailable: 'Wildcard already spent (visible in chip history).', moves: [], hits: 0, total: null, perGw: [], notes: [], unknowns: [] };
    var budget = squad.reduce(function (z, p) { return z + p.sell; }, 0) + bank;
    // skeleton: cheapest legal 15 (club-cap aware), then greedy upgrades
    var byPosCheap = {};
    for (var pos = 1; pos <= 4; pos++) {
      byPosCheap[pos] = poolPlayers.filter(function (p) { return p.pos === pos && p.rated; })
        .sort(function (a, b) { return a.cost - b.cost; });
    }
    var skel = [], counts = {};
    for (var q = 1; q <= 4; q++) {
      var n = SQUAD_SHAPE[q], taken = 0;
      for (var i = 0; i < byPosCheap[q].length && taken < n; i++) {
        var p = byPosCheap[q][i];
        if ((counts[p.team] || 0) >= CLUB_CAP) continue;
        skel.push({ id: p.id, pos: p.pos, team: p.team, cost: p.cost, sell: p.cost, rated: true, xpgw: p.xpgw, name: p.name });
        counts[p.team] = (counts[p.team] || 0) + 1; taken++;
      }
      if (taken < n) return { key: 'wildcard', label: 'Wildcard restructure', available: false,
        reasonUnavailable: 'Could not build a legal skeleton squad from rated players.', moves: [], hits: 0, total: null, perGw: [], notes: [], unknowns: [] };
    }
    var cur = skel;
    var spent = cur.reduce(function (z, p) { return z + p.cost; }, 0);
    var horizon = function (p) { return gws.reduce(function (z, g) { return z + xpOf(p, g); }, 0); };
    for (var iter = 0; iter < 60; iter++) {
      var bestUp = null;
      for (var o = 0; o < cur.length; o++) {
        var out = cur[o];
        for (var i = 0; i < cands.length; i++) {
          var inn = cands[i];
          if (inn.pos !== out.pos || cur.some(function (p) { return p.id === inn.id; })) continue;
          var extra = inn.cost - out.cost;
          if (spent + extra > budget + 1e-9) continue;
          var trial = applySwap(cur, out.id, inn);
          if (!legalClubCap(trial)) continue;
          var gain = horizon(inn) - horizon(out);
          if (gain > 0 && (!bestUp || gain > bestUp.gain)) bestUp = { out: out, inn: inn, extra: extra, gain: gain };
        }
      }
      if (!bestUp) break;
      cur = applySwap(cur, bestUp.out.id, bestUp.inn);
      spent += bestUp.extra;
    }
    var h = horizonXp(cur, gws);
    return { key: 'wildcard', label: 'Wildcard restructure', available: true,
      moves: [{ gw: gws[0], out: 'Full squad rebuild', inn: 'Optimal 15 under budget', price: +(spent - (budget - bank)).toFixed(2), hit: false }],
      hits: 0, total: h.total, perGw: h.perGw,
      notes: ['Rebuilt 15 costs ' + spent.toFixed(1) + ' of ' + budget.toFixed(1) + ' available (sells + bank).',
              'Timing: played GW' + gws[0] + ' in this comparison. Later entry is possible but unmodelled here.'],
      unknowns: ['A real wildcard is irreversible and reprices nightly - this is a sketch, not a squad to copy'] };
  }

  /* Grounded sell values from the public transfer history + official sell rule.
     pickIds: current squad element ids. transfers: entry/{id}/transfers/ rows.
     gw1Value/nowCost: {elementId: tenths}. lastGw: last FINISHED gameweek -
     transfers for later events are ignored (feed cannot see past the lock).
     Rule (official): profit = now - purchase; sell = purchase + floor(profit/2)
     when now > purchase, else sell = now. Purchase comes from the latest
     in-transfer at or before lastGw; players never transferred in use the GW1
     price (initial-squad assumption, labeled in the UI). When history is
     inconsistent (sold after the latest buy yet still in the squad) or missing,
     the player is unresolved and priced at current cost with basis 'cost'.
     Returns { byId: {id: {sell (tenths int|null), basis}}, unresolved }. */
  function computeSells(pickIds, transfers, gw1Value, nowCost, lastGw) {
    var inAt = {}, outAt = {};
    (transfers || []).forEach(function (t) {
      if (!t || typeof t.event !== 'number' || t.event > lastGw) return;
      if (typeof t.element_in === 'number' && typeof t.element_in_cost === 'number') {
        if (inAt[t.element_in] === undefined || t.event >= inAt[t.element_in].event)
          inAt[t.element_in] = { event: t.event, cost: t.element_in_cost };
      }
      if (typeof t.element_out === 'number') {
        if (outAt[t.element_out] === undefined || t.event > outAt[t.element_out])
          outAt[t.element_out] = t.event;
      }
    });
    var byId = {}, unresolved = 0;
    pickIds.forEach(function (id) {
      var now = nowCost[id];
      var hasNow = typeof now === 'number' && Number.isFinite(now);
      var purchase = null, basis = 'cost';
      if (inAt[id] !== undefined && !(outAt[id] !== undefined && outAt[id] > inAt[id].event)) {
        purchase = inAt[id].cost; basis = 'history';
      } else if (inAt[id] === undefined && gw1Value && typeof gw1Value[id] === 'number') {
        purchase = gw1Value[id]; basis = 'gw1';
      }
      if (purchase === null || !hasNow) {
        unresolved++;
        byId[id] = { sell: hasNow ? now : null, basis: 'cost' };
        return;
      }
      var profit = now - purchase;
      byId[id] = { sell: profit > 0 ? purchase + Math.floor(profit / 2) : now, basis: basis };
    });
    return { byId: byId, unresolved: unresolved };
  }

  function compare(squadPicks, poolPlayers, opts) {
    var gws = opts.gws;
    var squad = toEngine(squadPicks, poolPlayers);
    var cands = candidates(Object.keys(poolPlayers).map(function (k) { return poolPlayers[k]; }), gws, 8);
    var bank = opts.bank, fts = opts.fts;
    return [stratRoll(squad, gws),
            stratSingleFix(squad, cands, bank, fts, gws),
            stratAggressive(squad, cands, bank, fts, gws, 2),
            stratWildcard(squad, cands, Object.keys(poolPlayers).map(function (k) { return poolPlayers[k]; }), bank, opts.chips, gws)];
  }

  return { compare: compare, bestXI: bestXI, horizonXp: horizonXp, legalClubCap: legalClubCap,
           candidates: candidates, toEngine: toEngine, computeSells: computeSells,
           _internals: { xpOf: xpOf, bestSwap: bestSwap, FORMATIONS: FORMATIONS } };
});
