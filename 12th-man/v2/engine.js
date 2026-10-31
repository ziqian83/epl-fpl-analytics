/* The 12th Man v2 - decision engine (fresh brief 31 Oct 2026).
   Verdict first, then plays, chips, evidence and outsiders. Design: docs/10.
   Pure functions over v2/data/pool.json + the user's squad; no DOM, no fetches,
   so the same file runs in the browser (window.T12V2) and under node (tests).
   Every projection is a WEAK signal (docs/09: pairwise +0.5-1.5pp over naive,
   MAE ~2.3/player-GW): edges under ~1 point sit inside a chosen decision margin and are labeled so.
   Known simplifications (labeled in the UI): prices frozen across the horizon,
   trailing features held constant, transfers settle at each GW start, unrated
   players contribute 0 xP and are counted, never hidden. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.T12V2 = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  var SQUAD_SHAPE = { 1: 2, 2: 5, 3: 5, 4: 3 };
  var CLUB_CAP = 3;
  var FT_MAX = 5;
  var HIT_COST = 4;
  var DECISION_MARGIN = 1.0; // chosen sensitivity line for horizon edges (docs/09 MAE ~2.3/player-GW); NOT a calibrated noise threshold
  var FORMATIONS = [[3, 4, 3], [3, 5, 2], [4, 3, 3], [4, 4, 2], [4, 5, 1], [5, 2, 3], [5, 3, 2], [5, 4, 1]];
  var CHIP_LABELS = { wildcard: 'Wildcard', freehit: 'Free hit', bboost: 'Bench boost', '3xc': 'Triple captain' };

  function xpOf(player, gw) {
    if (!player || !player.rated || !player.xpgw) return 0;
    return player.xpgw[gw] || 0;
  }

  /* ---------- evidence: form, consistency, one-week wonder (docs/10) ---------- */
  function evidence(p) {
    var recent = (p && p.recent) || [];
    var last6 = recent.slice(-6);
    var played = last6.filter(function (r) { return r.mins >= 45; });
    var returns = played.filter(function (r) { return r.pts >= 5; }).length;
    var last = recent.length ? recent[recent.length - 1] : null;
    var prior = recent.slice(-5, -1);
    var priorForm = prior.length ? prior.reduce(function (z, r) { return z + r.pts; }, 0) / prior.length : 0;
    var last2 = recent.slice(-2);
    var last3 = recent.slice(-3);
    var mins3 = last3.length ? last3.reduce(function (z, r) { return z + r.mins; }, 0) / last3.length : null;
    var att = p && p.pos >= 3; // MID/FWD only for xGI-based flags
    return {
      played: played.length,
      returns: returns,
      consistency: played.length ? returns / played.length : null,
      form4: p && p.f ? p.f.pts4 : null,
      form2: p && p.f ? p.f.pts2 : null,
      spike: !!(att && last && prior.length === 4 && last.pts >= 8 && last.xgi <= 0.5 && (last.pts - priorForm) >= 5),
      quiet: !!(att && last2.length === 2 && last2.reduce(function (z, r) { return z + r.xgi; }, 0) >= 1.5 && last2.reduce(function (z, r) { return z + r.pts; }, 0) <= 4),
      rotation: !!(mins3 !== null && mins3 < 60 && last6.some(function (r) { return r.mins > 0; })),
      lastGw: last,
    };
  }

  /* ---------- XI / squad mechanics ---------- */
  function bestXI(squadPlayers, gw) {
    var best = null;
    for (var f = 0; f < FORMATIONS.length; f++) {
      var need = { 1: 1, 2: FORMATIONS[f][0], 3: FORMATIONS[f][1], 4: FORMATIONS[f][2] };
      var xi = [], ok = true;
      for (var pos = 1; pos <= 4; pos++) {
        var inPos = squadPlayers.filter(function (p) { return p.pos === pos; })
          .sort(function (a, b) { return xpOf(b, gw) - xpOf(a, gw); });
        if (inPos.length < need[pos]) { ok = false; break; }
        xi = xi.concat(inPos.slice(0, need[pos]));
      }
      if (!ok) continue;
      var base = xi.reduce(function (z, p) { return z + xpOf(p, gw); }, 0);
      if (!best || base > best.base) best = { base: base, xi: xi, formation: FORMATIONS[f] };
    }
    if (!best) return { xp: 0, xiIds: [], captainId: null, unratedInXi: 0, formation: null };
    var cap = best.xi.slice().sort(function (a, b) { return xpOf(b, gw) - xpOf(a, gw); })[0];
    return { xp: +(best.base + xpOf(cap, gw)).toFixed(2), xiIds: best.xi.map(function (p) { return p.id; }),
      captainId: cap ? cap.id : null, captainXp: cap ? xpOf(cap, gw) : 0,
      unratedInXi: best.xi.filter(function (p) { return !p.rated; }).length, formation: best.formation };
  }

  function legalClubCap(players) {
    var c = {};
    players.forEach(function (p) { c[p.team] = (c[p.team] || 0) + 1; });
    return Object.keys(c).every(function (t) { return c[t] <= CLUB_CAP; });
  }

  function candidates(poolPlayers, gws, perPos) {
    var horizon = function (p) { return gws.reduce(function (z, g) { return z + xpOf(p, g); }, 0); };
    var out = [];
    for (var pos = 1; pos <= 4; pos++) {
      var inPos = poolPlayers.filter(function (p) { return p.pos === pos && p.rated; });
      var seen = {};
      inPos.slice().sort(function (a, b) { return horizon(b) - horizon(a); }).slice(0, perPos)
        .concat(inPos.slice().sort(function (a, b) { return a.cost - b.cost; }).slice(0, 2))
        .forEach(function (p) { if (!seen[p.id]) { seen[p.id] = 1; out.push(p); } });
    }
    return out;
  }

  /* Greedy estimate of the best affordable free-hit squad for one gameweek.
     Budget = sum of current sell values + bank (a real free hit sells the whole
     squad at sell price). Fills legal squad quotas by xP, club cap 3, under
     budget. This is a greedy ESTIMATE of the optimized one-week uplift, not a
     proof of the optimum. */
  function freeHitXi(squad, poolArr, bank, gw) {
    var budget = squad.reduce(function (z, p) { return z + (p.sell || 0); }, 0) + bank;
    var quota = { 1: 2, 2: 5, 3: 5, 4: 3 };
    var picked = [], spent = 0, clubs = {};
    var byPos = {};
    poolArr.forEach(function (p) {
      if (!p.rated || xpOf(p, gw) <= 0) return;
      (byPos[p.pos] = byPos[p.pos] || []).push(p);
    });
    [1, 2, 3, 4].forEach(function (pos) {
      var list = (byPos[pos] || []).slice().sort(function (a, b) { return xpOf(b, gw) - xpOf(a, gw); });
      var need = quota[pos], got = 0;
      list.forEach(function (p) {
        if (got >= need || (clubs[p.team] || 0) >= CLUB_CAP || spent + p.cost > budget) return;
        picked.push(p); spent += p.cost; clubs[p.team] = (clubs[p.team] || 0) + 1; got++;
      });
      if (got < need) { // budget forced cheaper cover: fill legally with the cheapest remaining
        list.slice().sort(function (a, b) { return a.cost - b.cost; }).forEach(function (p) {
          if (got >= need || picked.indexOf(p) >= 0 || (clubs[p.team] || 0) >= CLUB_CAP || spent + p.cost > budget) return;
          picked.push(p); spent += p.cost; clubs[p.team] = (clubs[p.team] || 0) + 1; got++;
        });
      }
    });
    if (picked.length < 15) return null;
    var xi = bestXI(picked, gw);
    return { xp: xi.xp, spent: +spent.toFixed(1), budget: +budget.toFixed(1) };
  }

  function applySwap(squad, outId, inPlayer) {
    return squad.map(function (p) {
      if (p.id !== outId) return p;
      return { id: inPlayer.id, pos: inPlayer.pos, team: inPlayer.team, cost: inPlayer.cost,
               sell: inPlayer.cost, rated: inPlayer.rated, xpgw: inPlayer.xpgw, name: inPlayer.name, slot: p.slot };
    });
  }

  function horizonXp(squad, gws) {
    var perGw = gws.map(function (gw) { return bestXI(squad, gw); });
    return { total: +perGw.reduce(function (z, r) { return z + r.xp; }, 0).toFixed(2), perGw: perGw };
  }

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
      return { id: pk.id, slot: pk.slot || 0, pos: pl ? pl.pos : pk.pos, team: pl ? pl.team : pk.team,
               cost: pl ? pl.cost : pk.cost, sell: sellKnown ? pk.selling : (pl ? pl.cost : 0), sellAssumed: !sellKnown,
               rated: !!(pl && pl.rated), xpgw: pl ? pl.xpgw : null, name: pl ? pl.name : ('Player #' + pk.id) };
    });
  }

  /* ---------- Grounded sell values (12th Man's own, carried from v1) ---------- */
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

  /* Coverage: which squad players carry NO model projection (missing estimate,
     not a real zero). A real zero is a rated player projected 0; a missing
     projection means the model cannot rank this player at all (docs/10). */
  function coverage(squad, poolArr) {
    var missing = squad.filter(function (p) { return !p.rated; }).map(function (p) {
      var pl = poolArr.find(function (q) { return q.id === p.id; });
      var rec = (pl && pl.recent) || [];
      var last3 = rec.slice(-3);
      var mins3 = last3.reduce(function (z, r) { return z + r.mins; }, 0);
      return { id: p.id, name: p.name, slot: p.slot,
               reason: (pl && pl.reason) || 'not rated',
               mins3: mins3,
               pts3: last3.reduce(function (z, r) { return z + r.pts; }, 0),
               epNext: (pl && pl.ep_next != null) ? Number(pl.ep_next) : null };
    });
    var shifters = missing.filter(function (m) { return m.mins3 >= 45; });
    return { total: squad.length, missing: missing, shifters: shifters, couldShift: shifters.length > 0 };
  }

  /* Sensitivity: for a missing-projection squad player, at what imputed this-GW
     xP would the verdict class, the named fix, or XI membership change? A sweep
     over the engine's own machinery - no invented coefficient, no imputed value
     is used in any displayed number (docs/14). */
  function sensitivity(squad, poolArr, gw, bank, playerId) {
    var base = assess(squad, poolArr, gw, bank);
    var baseFix = base.bestFix ? base.bestFix.out + '>' + base.bestFix.inn : 'none';
    var entersXiAt = null, fixChangesAt = null, clsChangesAt = null;
    for (var v = 0.5; v <= 10.01; v += 0.5) {
      var mod = squad.map(function (p) {
        if (p.id !== playerId) return p;
        var xpgw = {}; xpgw[gw] = v;
        return Object.assign({}, p, { rated: true, xpgw: xpgw });
      });
      var a = assess(mod, poolArr, gw, bank);
      if (entersXiAt === null && a.xiIds.indexOf(playerId) >= 0) entersXiAt = v;
      var fix = a.bestFix ? a.bestFix.out + '>' + a.bestFix.inn : 'none';
      if (fixChangesAt === null && fix !== baseFix) fixChangesAt = v;
      if (clsChangesAt === null && a.cls !== base.cls) clsChangesAt = v;
    }
    return { playerId: playerId, entersXiAt: entersXiAt, fixChangesAt: fixChangesAt, clsChangesAt: clsChangesAt,
             baseFix: base.bestFix ? base.bestFix.out + ' -> ' + base.bestFix.inn : null };
  }

  /* ---------- the verdict: good enough, or fix? (docs/10) ---------- */
  function assess(squad, poolArr, gw, bank) {
    var cands = candidates(poolArr, [gw], 8);
    var cov = coverage(squad, poolArr);
    var xi = bestXI(squad, gw);
    var xiPlayers = squad.filter(function (p) { return xi.xiIds.indexOf(p.id) >= 0; });
    var flagged = xiPlayers.filter(function (p) {
      var pl = poolArr.find(function (q) { return q.id === p.id; });
      var news = pl && pl.news && /injur|doubt|suspend|ban/i.test(pl.news);
      var unavailable = pl && typeof pl.status === 'string' && pl.status !== 'a';
      var blank = p.rated && xpOf(p, gw) === 0;
      return news || unavailable || blank;
    });
    var best1 = bestSwap(squad, cands, bank, [gw]);
    var gain = best1 ? best1.gain : 0;
    var fixWord = cov.missing.length ? 'Best rated-only fix' : 'Best single fix';
    var cls, label, why;
    if (gain < 0.75 && flagged.length === 0) {
      cls = 'good'; label = 'Good enough this week';
      why = (cov.couldShift ? 'Among rated players, no' : 'No') + ' legal one-transfer fix inside your budget gains three-quarters of a point this week, and no starter carries team-news risk. Under a weak projection, that is a hold signal, not a hidden problem.' +
        (cov.couldShift ? ' Coverage is partial (below), so this class can shift.' : '');
    } else if (gain < 2.0 && flagged.length <= 1) {
      cls = 'fix'; label = 'One fix worth your judgement';
      why = 'The model sees a real but not decisive improvement available' +
        (flagged.length ? ', and ' + flagged.length + (flagged.length === 1 ? ' starter carries' : ' starters carry') + ' news or a blank' : '') + '.' +
        (cov.missing.length ? ' The named fix compares rated players only.' : '');
    } else {
      cls = 'surgery'; label = 'Structural issues worth modelling';
      why = fixWord + ' projects +' + gain.toFixed(2) + ' xP this week' +
        (flagged.length ? ' and ' + flagged.length + (flagged.length === 1 ? ' starter is' : ' starters are') + ' flagged (news or blank)' : '') + '.';
    }
    return { cls: cls, label: label, why: why, xiXp: xi.xp, xiIds: xi.xiIds, captainId: xi.captainId,
      unratedInXi: xi.unratedInXi, formation: xi.formation,
      bestFix: best1 ? { out: best1.out.name, inn: best1.inn.name, price: best1.price, gain: best1.gain } : null,
      flagged: flagged.map(function (p) { return p.name; }) };
  }

  /* ---------- chips: windows from official rules + used history ---------- */
  function chipState(chipWindows, usedChips, gw) {
    var used = {}, usedEv = {};
    (usedChips || []).forEach(function (c) {
      used[c.name] = (used[c.name] || 0) + 1;
      usedEv[c.name] = Math.max(usedEv[c.name] || 0, c.event || 0);
    });
    var names = ['wildcard', 'freehit', 'bboost', '3xc'];
    return names.map(function (nm) {
      var copies = (chipWindows || []).filter(function (c) { return c.name === nm; });
      var spent = used[nm] || 0;
      var liveCopy = copies.find(function (c) { return gw >= c.start && gw <= c.stop && spent < copies.indexOf(c) + 1; });
      var futureCopy = copies.find(function (c) { return c.start > gw && spent < copies.indexOf(c) + 1; });
      // Official rule: a Free Hit cannot be played in consecutive Gameweeks (e.g. FH in GW19 locks the second copy until GW21).
      if (nm === 'freehit' && usedEv.freehit && gw === usedEv.freehit + 1) {
        var nxt = copies.find(function (c) { return c.start > usedEv.freehit && spent < copies.indexOf(c) + 1; });
        return { name: nm, label: CHIP_LABELS[nm], state: 'locked', unlocks: nxt ? Math.max(nxt.start, gw + 1) : gw + 1,
                 note: 'Played in GW' + usedEv.freehit + ' - free hits cannot run in consecutive gameweeks.' };
      }
      if (liveCopy) return { name: nm, label: CHIP_LABELS[nm], state: 'live', expires: liveCopy.stop, window: liveCopy };
      if (futureCopy) return { name: nm, label: CHIP_LABELS[nm], state: 'future', unlocks: futureCopy.start, window: futureCopy };
      return { name: nm, label: CHIP_LABELS[nm], state: 'spent', window: null };
    });
  }

  /* Free transfers held, derived from entry history under current official rules:
     1 FT per GW, unused carry capped at 5, saved FTs retained through wildcard/free hit
     (chip-week transfers do not consume FTs). Recurrence over finished GWs only. */
  function deriveFT(hist) {
    var chipGw = {};
    ((hist && hist.chips) || []).forEach(function (c) { if (c.name === 'wildcard' || c.name === 'freehit') chipGw[c.event] = true; });
    var ft = 1;
    ((hist && hist.current) || []).forEach(function (r) {
      var used = chipGw[r.event] ? 0 : (r.event_transfers || 0);
      ft = Math.min(FT_MAX, ft - used + 1);
    });
    return ft;
  }

  function chipVerdicts(squad, poolArr, chips, gw, horizonGws, bank) {
    var out = {};
    var bench = squad.filter(function (p) { return p.slot > 11; });
    var benchXp = bench.reduce(function (z, p) { return z + xpOf(p, gw); }, 0);
    var xi = bestXI(squad, gw);
    var benchByGw = horizonGws.map(function (g) {
      return { gw: g, xp: +bench.reduce(function (z, p) { return z + xpOf(p, g); }, 0).toFixed(2) };
    });
    var betterBench = benchByGw.some(function (b) { return b.gw > gw && b.xp > benchXp; });
    var capXp = xi.captainXp || 0;
    var capByGw = horizonGws.map(function (g) { var x = bestXI(squad, g); return { gw: g, xp: x.captainXp || 0 }; });
    var betterCap = capByGw.some(function (b) { return b.gw > gw && b.xp > capXp; });
    var blanks = squad.filter(function (p) {
      return xi.xiIds.indexOf(p.id) >= 0 && p.rated && xpOf(p, gw) === 0;
    }).length;
    var newsOut = squad.filter(function (p) {
      if (xi.xiIds.indexOf(p.id) < 0) return false;
      var pl = poolArr.find(function (q) { return q.id === p.id; });
      return pl && ((pl.news && /injur|doubt|suspend|ban/i.test(pl.news)) || (typeof pl.status === 'string' && pl.status !== 'a'));
    }).length;

    chips.forEach(function (c) {
      if (c.state !== 'live') { out[c.name] = { state: c.state, expires: c.expires, unlocks: c.unlocks }; return; }
      if (c.name === 'bboost') {
        var benchMissing = bench.filter(function (p) { return !p.rated; });
        if (benchMissing.length) {
          out.bboost = { state: 'live', expires: c.expires, benchXp: +benchXp.toFixed(2), benchByGw: benchByGw,
            verdict: 'withheld',
            why: 'Bench projects ' + benchXp.toFixed(1) + ' xP this week counting rated bench players only - a partial estimate, not a lower bound. ' +
              benchMissing.map(function (p) { return p.name; }).join(', ') +
              (benchMissing.length === 1 ? ' carries' : ' carry') + ' no projection, which could raise or lower the total, and bench order is interlocked with the XI, so no candidate/borderline/hold call is made. Expires after GW' + c.expires + '.' };
        } else {
          out.bboost = { state: 'live', expires: c.expires, benchXp: +benchXp.toFixed(2), benchByGw: benchByGw,
            verdict: benchXp >= 12 ? 'candidate' : (benchXp >= 9 ? 'borderline' : 'hold'),
            why: benchXp >= 12
              ? 'Bench projects ' + benchXp.toFixed(1) + ' xP this week' + (betterBench ? ' - a later week in the horizon projects even higher, so compare before playing' : ' - as strong as the model sees on the horizon') + '. The 12/9 xP bars are judgement lines, not calibrated thresholds.'
              : benchXp >= 9
                ? 'Bench projects ' + benchXp.toFixed(1) + ' xP - playable, but ' + (betterBench ? 'a later horizon week projects higher' : 'not a standout week') + '. Bars are judgement lines, not calibrated.'
                : 'Bench projects only ' + benchXp.toFixed(1) + ' xP this week - weak week for it. Expires after GW' + c.expires + '.' };
        }
      } else if (c.name === '3xc') {
        out['3xc'] = { state: 'live', expires: c.expires, capXp: +capXp.toFixed(2), capByGw: capByGw,
          verdict: capXp >= 7 ? 'candidate' : 'hold',
          why: capXp >= 7
            ? 'Your best starter projects ' + capXp.toFixed(1) + ' xP' + (betterCap ? ' - a later week projects a better captain spot' : ' - the strongest captain spot on the visible horizon') + '. Triple is a one-week multiplier on one player: variance-heavy even when the read is right. The 7 xP bar is a judgement line, not calibrated.'
            : 'Best starter projects ' + capXp.toFixed(1) + ' xP - no standout week. A double gameweek is the classic spot; none is flagged in this horizon. Expires after GW' + c.expires + '.' };
      } else if (c.name === 'freehit') {
        var fh = freeHitXi(squad, poolArr, bank || 0, gw);
        var fhUplift = fh ? +(fh.xp - xi.xp).toFixed(2) : null;
        out.freehit = { state: 'live', expires: c.expires, blanks: blanks, newsOut: newsOut,
          uplift: fhUplift, fhXiXp: fh ? fh.xp : null,
          verdict: (fhUplift !== null && fhUplift >= 2) ? 'candidate' : 'hold',
          why: fhUplift === null
            ? 'Could not build a legal free-hit squad inside the estimated budget - treat this card as unknown, not as a hold.'
            : (fhUplift >= 2
              ? 'Playing it this week projects +' + fhUplift.toFixed(1) + ' xP over your current XI (greedy best-affordable-squad estimate on weak xP, not a proven optimum). The certain cost is the copy itself: expires after GW' + c.expires + ', next copy unlocks GW20. Whether +' + fhUplift.toFixed(1) + ' now beats saving it for a worse week is your call. The 2 xP bar is a judgement line, not calibrated.'
              : 'Playing it this week projects only +' + Math.max(0, fhUplift).toFixed(1) + ' xP over your current XI (greedy estimate), and ' + (blanks + newsOut) + ' starter(s) project 0 or carry news. The certain cost of playing is the copy itself (expires after GW' + c.expires + '). Holding is not proven optimal either - a worse future week simply is not visible yet. The 2 xP bar is a judgement line, not calibrated.') };
      } else if (c.name === 'wildcard') {
        out.wildcard = { state: 'live', expires: c.expires }; // structural verdict rides on the wildcard plan card
      }
    });
    return out;
  }

  /* ---------- the plays (this GW and horizon lenses, costs explicit) ---------- */
  function plans(squad, poolArr, opts) {
    var gws = opts.gws, gw = gws[0], bank = opts.bank, fts = opts.fts;
    var cands = candidates(poolArr, gws, 8);
    var hold = horizonXp(squad, gws);
    var noise = 'Edges under ~' + DECISION_MARGIN.toFixed(0) + ' xP sit inside the decision margin of a weak model (mean error ~2.3 per player-GW, pairwise lift ~1pt over persistence in held-out seasons) - shown for completeness, not as a reason to act. The bar is a chosen sensitivity line, not a calibrated threshold or measured noise band.';

    // Hold
    var holdPlan = { key: 'hold', label: 'Hold - roll the transfer', certain: 0,
      thisGw: hold.perGw[0].xp, horizon: hold.total, moves: [],
      benefit: 'Banks a free transfer (carry cap ' + FT_MAX + ') and a week of price and team-news information.',
      cost: 'Foregoes any fix this week. The cost is the best fix you did not make - shown on the other cards.',
      uncertainty: noise };

    // One fix
    var sw = bestSwap(squad, cands, bank, gws);
    var swGw = bestSwap(squad, cands, bank, [gw]);
    var singlePlan;
    if (fts < 1) {
      singlePlan = { key: 'single', label: 'One targeted fix', available: false,
        why: 'Needs 1 free transfer; you have confirmed 0. A move is a -4 hit - see the hits card.' };
    } else if (!sw) {
      singlePlan = { key: 'single', label: 'One targeted fix', available: true, certain: 0,
        thisGw: hold.perGw[0].xp, horizon: hold.total, moves: [],
        benefit: 'No legal swap inside budget and the club cap improves the horizon projection - this play collapses into Hold.',
        cost: 'None.', uncertainty: noise };
    } else {
      var next = applySwap(squad, sw.out.id, sw.inn);
      var h = horizonXp(next, gws);
      var thisGwDelta = swGw ? swGw.gain : (h.perGw[0].xp - hold.perGw[0].xp);
      var horizonDelta = +(h.total - hold.total).toFixed(2);
      singlePlan = { key: 'single', label: 'One targeted fix', available: true, certain: 0,
        thisGw: h.perGw[0].xp, horizon: h.total,
        moves: [{ gw: gw, out: sw.out.name, inn: sw.inn.name, price: sw.price, hit: false }],
        gainThisGw: +thisGwDelta.toFixed(2), gainHorizon: horizonDelta,
        conflict: (thisGwDelta > 0.25 && horizonDelta < -0.25) || (thisGwDelta < -0.25 && horizonDelta > 0.25),
        benefit: '+' + thisGwDelta.toFixed(2) + ' xP this week, +' + horizonDelta.toFixed(2) + ' over the horizon (weak estimates). Keeps transfers flowing from GW' + (gw + 1) + '.',
        cost: 'Spends 1 free transfer. ' + sw.inn.name + ' sells back at purchase price if it goes wrong (no half-profit yet).',
        uncertainty: noise };
    }

    // More transfers if the numbers back it (his brief) - hits only past free ones
    var cur = squad.slice(), cash = bank, free = fts, hits = 0, moves = [];
    for (var g = 0; g < gws.length; g++) {
      var remaining = gws.slice(g);
      while (true) {
        var s2 = bestSwap(cur, candidates(poolArr, remaining, 8), cash, remaining);
        if (!s2) break;
        var isHit = free < 1;
        if (isHit && hits >= 2) break;
        if (isHit && s2.gain <= HIT_COST) break; // a hit must clear its certain cost in weak xP
        cur = applySwap(cur, s2.out.id, s2.inn);
        cash -= s2.price;
        moves.push({ gw: remaining[0], out: s2.out.name, inn: s2.inn.name, price: s2.price, hit: isHit });
        if (isHit) hits++; else free--;
      }
      free = Math.min(free + 1, FT_MAX);
    }
    var ah = horizonXp(cur, gws);
    var hitsGw1 = moves.filter(function (m) { return m.gw === gw && m.hit; }).length;
    var aggrPlan = { key: 'aggr', label: 'More moves, hits if needed', available: true,
      certain: hits * HIT_COST, thisGw: +(ah.perGw[0].xp - hitsGw1 * HIT_COST).toFixed(2),
      horizon: +(ah.total - hits * HIT_COST).toFixed(2), moves: moves,
      gainThisGw: +(ah.perGw[0].xp - hitsGw1 * HIT_COST - hold.perGw[0].xp).toFixed(2),
      gainHorizon: +(ah.total - hits * HIT_COST - hold.total).toFixed(2),
      benefit: moves.length ? moves.length + ' move(s); every hit taken only because its projected gain cleared the certain -4.' : 'No move sequence beat its certain costs - this play collapses into Hold.',
      cost: hits ? '-' + (hits * HIT_COST) + ' certain points in hits.' : 'No certain cost.',
      uncertainty: 'The bar a hit must clear (>4 xP projected) is a judgement line, not a calibrated threshold. ' + noise };

    // Wildcard (chip) - availability handled by chipState; here the restructure sketch
    var wcPlan = { key: 'wildcard', label: 'Wildcard restructure', available: false,
      why: 'See the chips strip for wildcard state.' };
    var wcAvail = (opts.chipState || []).some(function (c) { return c.name === 'wildcard' && c.state === 'live'; });
    if (wcAvail) {
      var budget = squad.reduce(function (z, p) { return z + p.sell; }, 0) + bank;
      var byPosCheap = {};
      for (var pos = 1; pos <= 4; pos++) {
        byPosCheap[pos] = poolArr.filter(function (p) { return p.pos === pos && p.rated; })
          .sort(function (a, b) { return a.cost - b.cost; });
      }
      var skel = [], counts = {}, skelOk = true;
      for (var q = 1; q <= 4; q++) {
        var taken = 0;
        for (var i = 0; i < byPosCheap[q].length && taken < SQUAD_SHAPE[q]; i++) {
          var p = byPosCheap[q][i];
          if ((counts[p.team] || 0) >= CLUB_CAP) continue;
          skel.push({ id: p.id, pos: p.pos, team: p.team, cost: p.cost, sell: p.cost, rated: true, xpgw: p.xpgw, name: p.name, slot: 0 });
          counts[p.team] = (counts[p.team] || 0) + 1; taken++;
        }
        if (taken < SQUAD_SHAPE[q]) skelOk = false;
      }
      if (skelOk) {
        var wcur = skel, spent = wcur.reduce(function (z, p) { return z + p.cost; }, 0);
        var horizonOf = function (p) { return gws.reduce(function (z, g) { return z + xpOf(p, g); }, 0); };
        for (var iter = 0; iter < 60; iter++) {
          var bestUp = null;
          for (var o2 = 0; o2 < wcur.length; o2++) {
            var out2 = wcur[o2];
            for (var i2 = 0; i2 < cands.length; i2++) {
              var inn2 = cands[i2];
              if (inn2.pos !== out2.pos || wcur.some(function (p2) { return p2.id === inn2.id; })) continue;
              var extra = inn2.cost - out2.cost;
              if (spent + extra > budget + 1e-9) continue;
              var trial = applySwap(wcur, out2.id, inn2);
              if (!legalClubCap(trial)) continue;
              var gain2 = horizonOf(inn2) - horizonOf(out2);
              if (gain2 > 0 && (!bestUp || gain2 > bestUp.gain)) bestUp = { out: out2, inn: inn2, extra: extra, gain: gain2 };
            }
          }
          if (!bestUp) break;
          wcur = applySwap(wcur, bestUp.out.id, bestUp.inn);
          spent += bestUp.extra;
        }
        var wh = horizonXp(wcur, gws);
        var wGain = +(wh.total - hold.total).toFixed(2);
        wcPlan = { key: 'wildcard', label: 'Wildcard restructure', available: true, certain: 0,
          thisGw: wh.perGw[0].xp, horizon: wh.total,
          gainThisGw: +(wh.perGw[0].xp - hold.perGw[0].xp).toFixed(2), gainHorizon: wGain,
          moves: [{ gw: gw, out: 'Full squad rebuild', inn: 'Best 15 under budget', price: +(spent - (budget - bank)).toFixed(2), hit: false }],
          chipVerdict: wGain >= 8 ? 'candidate' : 'hold',
          benefit: '+' + wGain.toFixed(2) + ' horizon xP over holding (weak estimate). Rebuilt 15 costs ' + spent.toFixed(1) + ' of ' + budget.toFixed(1) + ' available.',
          cost: 'Irreversible once played. Every player rebought at current price - your accrued sell-value profit is spent. Second-half wildcard unlocks GW20 regardless.',
          uncertainty: 'A real wildcard reprices nightly and the model cannot see injuries ahead - this is a sketch of the ceiling, not a squad to copy. ' + noise };
      }
    }

    // Engine lean: best horizon net, but never over hold unless it clears the noise bar
    var list = [holdPlan, singlePlan, aggrPlan, wcPlan].filter(function (p) { return p.available !== false; });
    var lean = holdPlan;
    list.forEach(function (p) {
      if (p !== holdPlan && typeof p.horizon === 'number' && p.horizon > (lean.horizon || 0)) lean = p;
    });
    if (lean !== holdPlan && (lean.horizon - hold.total) < DECISION_MARGIN) lean = holdPlan;
    var leanWhy = lean === holdPlan
      ? 'No play clears the ~1 xP decision margin over holding on the horizon - holding is the honest lean, not inertia.'
      : lean.label + ' leads the horizon by +' + (lean.horizon - hold.total).toFixed(2) + ' xP net of certain costs. Weak signal: this orders the options, it does not make the call.';
    if (lean === aggrPlan && aggrPlan.moves.length > 1) {
      leanWhy += ' This plan re-optimises every future week on today\'s frozen data, so its edge compounds model error - it is the least certain number on the page, and most of its moves are future weeks you will re-decide with better information.';
    }
    return { plans: [holdPlan, singlePlan, aggrPlan, wcPlan], leanKey: lean.key, leanWhy: leanWhy };
  }

  /* ---------- who else should I have considered (his standing ask) ---------- */
  function whoElse(squad, poolArr, bank, gws, perPos) {
    var out = [];
    var horizon = function (p) { return gws.reduce(function (z, g) { return z + xpOf(p, g); }, 0); };
    for (var pos = 1; pos <= 4; pos++) {
      var mine = squad.filter(function (p) { return p.pos === pos; });
      var maxSell = Math.max.apply(null, mine.map(function (p) { return p.sell; }).concat([0]));
      var weakest = mine.slice().sort(function (a, b) { return horizon(a) - horizon(b); })[0];
      var budget = bank + maxSell;
      var seen = {};
      squad.forEach(function (p) { seen[p.id] = true; });
      var list = poolArr.filter(function (p) {
        return p.pos === pos && p.rated && !seen[p.id] && p.cost <= budget + 1e-9 &&
          !(p.news && /injur|doubt|suspend|ban/i.test(p.news));
      }).sort(function (a, b) { return horizon(b) - horizon(a); }).slice(0, perPos || 3);
      list.forEach(function (c) {
        out.push({ pos: pos, id: c.id, name: c.name, team: c.team, cost: c.cost,
          horizonXp: +horizon(c).toFixed(2), thisGwXp: xpOf(c, gws[0]),
          owned: c.selected_pct, epNext: c.ep_next, evidence: evidence(c),
          replaces: weakest ? weakest.name : null, replacesXp: weakest ? +horizon(weakest).toFixed(2) : null });
      });
    }
    return out;
  }

  return { evidence: evidence, coverage: coverage, sensitivity: sensitivity, assess: assess, chipState: chipState, deriveFT: deriveFT, chipVerdicts: chipVerdicts, freeHitXi: freeHitXi,
    plans: plans, whoElse: whoElse, bestXI: bestXI, horizonXp: horizonXp, legalClubCap: legalClubCap,
    candidates: candidates, toEngine: toEngine, computeSells: computeSells,
    DECISION_MARGIN: DECISION_MARGIN, CHIP_LABELS: CHIP_LABELS,
    _internals: { xpOf: xpOf, bestSwap: bestSwap, FORMATIONS: FORMATIONS } };
});
