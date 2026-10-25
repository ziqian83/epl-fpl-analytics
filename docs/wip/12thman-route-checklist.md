# 12th Man build - pending gates before any push of pipeline/page (working note, not for publication)

## Route grounding (per main 20:02) - must be answered in-repo before client-side squad loading ships
- [ ] Fetch route for squad data: name the service/operator explicitly (candidate: same-origin GitHub Pages + direct public FPL API from browser where CORS allows; else a named, terms-accepted relay - no unverified public proxy)
- [ ] FPL public API usage: acceptable-use posture documented (read-only, no auth, no scraping of private endpoints)
- [ ] No secrets, no OAuth, no PAT anywhere in client or Actions logs
- [ ] No upload of personal state (team ID stays in localStorage; squad fetch is read-only by ID)
- [ ] Zero cost: GitHub Actions free tier, public API, GitHub Pages

## Pipeline verification before pool.json is trusted (per main 19:52/20:02)
- [x] Runs end-to-end (~3s, 12 workers)
- [x] Output sane: GW9, deadline 2026-10-31T11:00Z, 199 eligible players, xP 0.89-4.87
- [x] oppstr=0 for BHA investigated: data-faithful (4 straight clean sheets GW4-7, live API)
- [ ] Coverage report: who is excluded and why (cold start, blanks, <180 mins) - page must say who is NOT rated
- [ ] Mid-season transfer handling verified with a real case when one occurs
- [ ] DGW aggregation verified with a real DGW when one occurs

## UI delivery gates (per main 20:07)
- [ ] Strategy comparison: hold / transfer / chip options side by side, estimates labeled unvalidated, never "optimal"
- [ ] Weak-signal presentation: no single headline plan, no fake precision on chips/captain/hits
- [ ] Desktop + mobile screenshots of real interactions
- [ ] Source-freshness + input-correction behavior demonstrated (stale pool notice, editable FT/bank)
- [ ] Nothing squad-revealing in repo; team ID never hardcoded
