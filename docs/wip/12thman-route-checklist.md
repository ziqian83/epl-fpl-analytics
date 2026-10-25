# 12th Man build - pending gates before any push of pipeline/page (working note, not for publication)

## Route grounding (per main 20:02) - must be answered in-repo before client-side squad loading ships
- [x] Fetch route DECIDED and TESTED 25 Oct: FPL API sends no CORS headers (verified), so browser-direct is impossible. Primary relay r.jina.ai (operator: Jina AI, published terms, free anonymous tier, GET-only, CORS origin echo verified) - works for entry, picks, history (verified with public ID 895045). Fallback allorigins.win (open source, gnuns/allorigins) for entry/history only - its fetch of the picks endpoint failed 4x (522/500), documented in client error path.
- [ ] FPL public API usage: acceptable-use posture documented (read-only, no auth, no scraping of private endpoints)
- [x] No secrets, no OAuth, no keys anywhere in the client; PATs are minted-used-deleted per push cycle and never touch the repo
- [x] Team ID in localStorage only, squad fetch read-only by ID; UI discloses the relay sees the ID in the request. Hardcoded the preview team ID removed from the page (was in the preview build)
- [x] Zero cost: public API + free relays + GitHub Pages/Actions free tier

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
