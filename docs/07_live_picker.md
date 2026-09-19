# Learn it with me: turning The Boot Room into a live picker

*Weekend module 1, built 19 September 2026.*

## What changed

The first Boot Room review was a photograph: useful, but fixed to Gameweek 4. The live picker is a small machine. Give it the FPL team ID, free transfers and money in the bank; it pulls the latest locked squad and next fixtures from the official public FPL feed, applies the written rules, and ranks transfer moves.

Open it at [`boot-room/picker/`](../boot-room/picker/).

## Why the browser does the work

A normal web page can request public data directly. That means this module needs no server, no database password and no ClickHouse credentials. The browser asks four public endpoints for:

- the current players, prices, flags and form;
- the next gameweek deadline and fixtures;
- the latest locked squad for team `4120529`;
- each shortlisted player's recent match history.

The page never writes to the FPL account. It is advice only.

## The stable-key rule survives

FPL's current-season endpoints use an `element` id, but that id changes between seasons. The picker keeps `player_code` as the player identity in its analysis. The element id is only the temporary address needed to request this season's live history.

That distinction sounds fussy until two seasons are joined and Mohamed Salah becomes the wrong person. A stable key is the label on the folder; an element id is the seat number for this year's flight.

## How a recommendation is made

The picker separates facts from judgment.

**Facts from the live feed**

- form in FPL points;
- consistency: the share of 60+ minute matches returning at least four points;
- recent expected goal involvement;
- next fixture difficulty;
- price, position, club and availability flag.

**Judgment in visible code**

- live form and consistency lead the score;
- fixture difficulty tilts a close call;
- value rewards output per million;
- an injury or unavailable flag is a penalty;
- a move must fit the bank, preserve the three-player club cap and match positions;
- paid moves must clear the four-point gate over the four-gameweek horizon;
- if no move earns its place, the answer is to bank the transfer.

This is deliberately a transparent heuristic, not a claim that one formula predicts football. The weights are written in the page source and can be challenged.

## Why free transfers are typed in

The public FPL feed exposes the squad and team value, but not a reliable live count of banked free transfers. Pretending otherwise would be a worse interface than one honest input. The module defaults to Ziqian's current three; change it before each run.

The same applies to money in the bank. The latest locked gameweek reports it, but a screenshot may be newer. The editable field lets the manager win when sources disagree.

## Screenshot fallback, without theatre

A screenshot can be selected when the public squad endpoint is unavailable. It stays inside the browser and is not uploaded. This lightweight module does not claim to read the pixels. It displays the filename and asks for manual verification rather than producing a confident answer from a picture it did not parse.

A later module could add on-device OCR, but only with a visible review step because one misread price can make an impossible transfer look valid.

## Run it

1. Open the live picker.
2. Check team ID `4120529`.
3. Enter the real free-transfer count and money in the bank.
4. Click **Run the picker**.
5. Read the 10-second answer first, then the hold/sell board.
6. Re-run after internationals and press conferences before committing transfers.

No install. No secret. No transfer is made for you.

## A browser-security wrinkle

The official FPL feed is public, but it does not always allow a web page on another domain to read it directly. That browser rule is called CORS. The picker tries the official URL first, then uses AllOrigins as a public read-only relay if the browser blocks the direct request. The relay receives only the public FPL URL, never a login, cookie or secret. If both routes fail, the picker stops instead of recycling stale data.

## Three squad jobs, not one bench bucket

The picker now labels each player as XI core, pseudo-fodder, or true fodder. Core players carry the weekly scoring load. Pseudo-fodder, such as Calvert-Lewin or Mitchell, are cheap but play real minutes; a hard fixture swing can put them on sell-watch and a soft run raises their floor. True fodder, such as Steele, Yalcouye or Davis, is cheap insurance and is protected from churn. Its fixture is still shown in quieter type because it matters when an injury triggers an auto-sub.

The bench is ranked every week as Sub 1, 2 and 3 using recent 60-minute appearances, form and the next fixture. This is separate from transfer value: true fodder can be protected from a transfer yet still be ordered intelligently if called on.

## Planning three to five gameweeks ahead

The page proposes a primary savings target and a runner-up from the whole player pool. It shows the five-week score, the funding gap, and the official FPL price-change signal. The target is not typed by the manager, so the alternative remains visible as a check on model bias.

FPL's official public feed now carries price-change progress, projections, likelihood, lock and calibration fields. Those official fields drive the warning; the picker does not scrape a community predictor or invent a probability.

The public locked-squad feed still does not reveal purchase or sale prices. Each owned player therefore gets an editable sell-value field, initially showing current list price. Replace it with the actual value on the FPL transfer screen before trusting affordability. This matters because FPL returns only half of a player's price profit when sold.
