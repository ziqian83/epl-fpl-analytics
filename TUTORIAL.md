# Learn With Me: How This Project Gets Built

This file is the beginner's companion to the project. Every time the project hits a new milestone, a new chapter lands here explaining what we did - and, just as important, why we did it that way - with the exact steps, so that by the end you could build something like it yourself.

No prior experience assumed. Jargon gets explained the first time it appears. If you know what an Excel pivot table is, you know enough to follow along.

## Chapters

1. **From zero to a GitHub repo**
2. **ClickHouse Cloud: your account and your first service**
3. **Loading data with the `url()` table function**
4. First queries and sanity checks - *coming as we build*
5. Building the season-aggregate table - *coming as we build*
6. The backtest - *coming as we build*
7. The ChatGPT data connector - *coming as we build*
8. The FPL picker - *coming as we build*

---

## Chapter 1: From zero to a GitHub repo

*What we did: created a public GitHub repository for this project, wrote a README that tells its story, and filed the working blueprint in a docs folder. This chapter walks through each of those steps the way you would do them yourself - and explains the reasoning behind every choice, because the choices are the transferable part. The keystrokes change from project to project; the judgment doesn't.*

### 1.1 What GitHub actually is, and why the project starts here

The accountant's version: GitHub is a shared drive for a project, except every save is a named checkpoint with a note and a timestamp. "Loaded 10 seasons of data." "Fixed the join bug." Each checkpoint is called a **commit**, and the full list of them is visible forever. You can rewind to any point. You can never lose work.

A project folder on GitHub is called a **repository** (everyone says "repo"). This project lives in one: `ziqian83/epl-fpl-analytics`.

**Why the repo comes first, before any data exists.** Two reasons. Practically, it gives the project one home - every script, note, and decision lands in the same place from day one, instead of being scattered across downloads folders and chat threads. Strategically, for a project that is half showcase, the repo IS the deliverable. "I built an analytics project" is a claim; a link where someone can see the data model, the backtest, and the thinking is proof. So the repo isn't where the work gets filed at the end - it's where the work happens from the start.

GitHub is free. The account behind this project's repo was created years ago and costs nothing.

### 1.2 Creating your account

1. Go to [github.com](https://github.com) and click **Sign up**.
2. Give it an email, a password, and a username. The username becomes part of every URL you ever share, so pick something you'd be happy to put on a resume. This project uses `ziqian83`, which is why its address is `github.com/ziqian83/epl-fpl-analytics`.
3. Verify the email when GitHub asks. Done - you have an account.

### 1.3 Creating the repo - and why each setting is what it is

1. Once signed in, click the **+** in the top-right corner, then **New repository**.
2. Three choices matter:
   - **Repository name** - short, lowercase, hyphens between words. We chose `epl-fpl-analytics` because it says exactly what's inside, in words a stranger would search for. Cutesy names age badly; descriptive names work as their own explanation.
   - **Description** - one line that appears under the repo name everywhere it shows up. Think of it as the caption under a photo. Ours compresses the whole pitch into one sentence, because on a list of search results that line is all a visitor reads before deciding whether to click.
   - **Public or Private** - Public means anyone with the link can see it (they cannot edit it - only you can). Private means only you and people you invite. **We chose Public on purpose:** for a showcase project, visibility is the point. The one rule for public repos: never put passwords, API keys, or private data in them. Ever. This project only ever contains public football data and SQL, so it's safe by design.
3. Tick **Add a README file** (more on what that is in a second) and click **Create repository**.

That is the whole ceremony. No software to install, nothing on your computer.

### 1.4 The README: your project's cover page - and why it was written before any data

Every repo has one special file: `README.md`. GitHub shows it on the repo's front page, automatically, nicely formatted - the way a magazine lays out its cover story.

When someone opens this project's link, the first thing they see is the README: the idea, the architecture, the data model, the plan. A stranger can understand the whole project in two minutes without opening a single other file.

**Why write the story before there's data to show?** Because the README is where the project's promises live. Writing it first forces the design to be coherent: if you can't explain the idea, the architecture, and the milestones on one page, the project isn't ready to build. It also makes the repo honest from day one - ours states plainly "Status: build in progress", with the plan and the bar the backtest has to beat, so the repo documents the journey rather than pretending to be a finished product. When the data lands, we update the status line; the story was already true.

**The mental model:** the repo is the filing cabinet, the README is the cover page taped to the front.

### 1.5 Markdown: formatting with plain characters

The `.md` in `README.md` stands for **Markdown** - a way of formatting text using plain characters, so the same file reads fine as raw text AND renders beautifully on the page. You only need four moves for now, and they are all used in this project's README:

| You type | You get |
| --- | --- |
| `# Big heading` | A large title (more `#`s = smaller heading: `##`, `###`) |
| `**important words**` | **important words** (bold) |
| `- an item` | A bullet point (one per line) |
| `[clickable text](https://example.com)` | A link, like [this project's blueprint](docs/blueprint.txt) |

That's it. When GitHub displays the file it hides the characters and shows the formatting. To see the raw characters behind any `.md` file on GitHub, click the **Code** view (the `<>` icon) when the file is open - flip between raw and rendered and the four moves above become obvious.

### 1.6 Adding and editing files, all in the browser - and why no command line

GitHub's command-line tooling (`git`) is what professionals use day to day, but **we deliberately do everything through the web interface**: nothing to install, every action visible on screen, and for a one-person project nothing is lost. The concepts (files, folders, commits) are identical; if you later learn `git`, Chapter 1 still maps one-to-one onto it.

**Create a new file:**
1. Open the repo, click **Add file** (top-right of the file list), then **Create new file**.
2. Type the filename at the top. To put a file inside a folder, type the folder name, then `/`, then the filename - `docs/blueprint.txt` creates a folder called `docs` containing `blueprint.txt`. Folders on GitHub are just names with slashes.
3. Paste or type the content into the big editor box.

**Edit an existing file:** open the file, click the pencil icon (top-right of the file view), make your changes.

**Save your work (this is the checkpoint):**
1. Scroll down to **Commit changes**. Remember: a commit is a named checkpoint.
2. The commit message box is the note on the checkpoint. Make it describe the change - `Add project tutorial chapter 1`, not `update file`. **This matters more than it looks:** the commit list is the audit trail, and its only value is that each note says what happened and why. Future-you (or a future employer scrolling the history) reads these notes as the story of how the project was built.
3. Leave **Commit directly to the main branch** selected (branches are for parallel versions of the work - a later chapter if we ever need them; with one person on a project, main is fine).
4. Click **Commit changes**.

Every edit lands in the repo's history immediately, and the README on the front page updates the moment you commit.

### 1.7 How this repo is organized - and why

- `README.md` - the cover page: the story, the plan, the milestones.
- `docs/blueprint.txt` - the full working blueprint: data sources, load script, backtest design. Working papers live in `docs/`, separate from the cover page, so a visitor gets the polished story up front and can dig into the workings if they want.
- `TUTORIAL.md` - this file.
- SQL scripts will join once the data warehouse is live - one file per major step, so each one can be replayed on its own. Small, single-purpose files beat one giant script: easier to follow, easier to rerun just the piece you need, and each becomes its own clearly-named checkpoint in the history.

### 1.8 Try it yourself

Create a private practice repo and run the whole Chapter 1 circuit on it:

1. Create a repo called `practice-sandbox`, set it to **Private** (so nobody sees your homework), and tick **Add a README file**.
2. Edit the README: give it a `#` title, one paragraph about anything (a hobby, a trip), one **bold** phrase, and a three-item bullet list. Commit with the message `Write my first README`.
3. Create a folder and file in one move: **Add file** > **Create new file**, name it `docs/notes.md`, write three lines, commit.
4. Open the repo's **commits** page (click the clock icon or "N commits" link on the front page) and find your three checkpoints with their notes. That list is the audit trail this chapter keeps talking about.

Fifteen minutes, and you've done everything this chapter describes. Chapter 2 picks up when the ClickHouse Cloud account goes live.


---

## Chapter 2: ClickHouse Cloud: your account and your first service

*What we did: signed up for ClickHouse Cloud - the database that powers this project - and created our first "service", a running database in the cloud, on a free trial that cannot bill us. By the end of this chapter you can create your own cloud database and will understand every choice in the setup wizard.*

### 2.1 What ClickHouse is, and why this project runs on it

ClickHouse is a database: software that stores tables and answers questions about them. Its specialty is **analytics** - questions that scan or summarize huge numbers of rows at once, like "total points per player per season across 254,000 rows." The accountant's version: it is the pivot table engine that never says the file is too large.

Why ClickHouse for this project, specifically:

1. **Zero install.** Everything happens in a web page - the SQL console - which fits the zero-code architecture in the [README](README.md).
2. **It is the warehouse the ChatGPT data connector plugs into.** That connector is the showcase story (chapter 7).
3. **It is genuinely fast** at exactly the questions the backtest asks.

One term you will see constantly: **SQL** (Structured Query Language) is the language you use to talk to databases. It reads more like English sentences than code: `SELECT` these columns `FROM` that table `WHERE` this is true. This project writes no programs - SQL statements pasted into a console are the whole build.

### 2.2 Signing up - and the email-alias trick worth stealing

1. Go to `console.clickhouse.cloud/signUp` and register with an email and a password.
2. The email we used is a Gmail **plus-alias**, and the trick is worth stealing for your whole digital life: if your address is `name@gmail.com`, then `name+anything@gmail.com` is the **same inbox**. Gmail ignores everything between the `+` and the `@`. So a signup under `ziqian83+epl@gmail.com` delivers to the usual inbox - no new mailbox to check.
3. Why bother, if the mail lands in the same place anyway? Because the alias gives each service its own identity while you keep one inbox. You can filter or search on it, you can tell exactly who leaked or sold an address when spam arrives addressed to it, and each trial or project account stays neatly labeled. It costs nothing and takes one extra word at signup.
4. Click the verification link in the email - the standard prove-you-own-the-inbox step.

### 2.3 Creating the service - what the wizard is really asking

The onboarding wizard's choices, translated:

- **Database = ClickHouse.** (They offer related products; we want the classic warehouse.)
- **Service name = `epl-playground`.** A **service** is your own database server, running on ClickHouse's computers. Think of it as renting a managed computer whose only job is to hold your tables and answer your queries - you never see the machine, only a console and a connection address.
- **Provider = AWS.** Whose computers it runs on (Amazon's). ClickHouse Cloud is a layer on top of a big cloud provider; AWS is the default and fine.
- **Region = Singapore (`ap-southeast-1`).** Where in the world the machine physically sits. Two reasons to choose deliberately: speed (nearer means a snappier console), and professional habit - data location matters in real corporate work (regulation, residency), so picking it on purpose even for a toy project builds the right reflex.
- **Scaling = default.** How big the machine is. The defaults are deliberately small, and a quarter-million rows is nothing for ClickHouse - you can grow later. On a trial, size is how fast you burn credits, so small is correct.

Click **Create service**, wait about two minutes while ClickHouse builds the machine in the background, and it appears in the console, running.

### 2.4 Trial mechanics - read this before anyone ever enters a card

New organizations get **$300 of credits and 30 days**. If you never add a payment method, the service simply **stops** when the trial ends. Nothing auto-charges - there is no card on file to charge.

We took the trial exactly as-is, for two reasons: the whole project costs a small fraction of those credits, and "stops unless you act" is precisely the failure mode a learner wants. The trials that hurt people are the ones that quietly convert to paid; this one can't.

### 2.5 Try it yourself

1. Sign up with a plus-alias and verify the email.
2. Create a service: name it after a project of your own, AWS, Singapore, default scaling.
3. Open the SQL console and run your first statement: `SELECT 1 + 1;` If it answers `2`, you own a cloud database.
4. Put the trial end date in your calendar. Treat cloud trials like any free-trial subscription: the person who notes the date never gets surprised.

---

## Chapter 3: Loading data with the url() table function

*What we did: loaded ten seasons of Premier League data - about a quarter of a million rows - into the warehouse by pasting one script into the SQL console. No downloads, no Python, no servers. This chapter explains the trick that makes that possible, the five tables it builds, and the verification habit that separates "it ran" from "it worked".*

### 3.1 The url() trick: query a CSV straight off the web

The traditional way to load data: download files, clean them, upload them, load them. ClickHouse's `url()` **table function** collapses all of that: it lets a query read a file at a web address as if the file were already a table. One statement says "take the CSV at this URL and insert it into this table," and ClickHouse fetches it over the web itself.

This is the project's superpower, because both data sources publish plain CSVs at stable URLs (the vaastav/Fantasy-Premier-League GitHub repo and football-data.co.uk). The entire data load is paste-and-run. The full script lives in the repo at [sql/epl_clickhouse_load.sql](sql/epl_clickhouse_load.sql): 37 `INSERT` statements (one per season per source), plus the table definitions and sanity checks this chapter walks through.

### 3.2 The five tables, and why they are shaped this way

First, the most important idea in data work: a table's **grain** is what one row represents. Say the grain out loud before building anything - nearly every confusion downstream is a grain confusion upstream.

- `epl_fpl_gameweeks` - one row per **player per gameweek** (~254k rows). The raw facts: minutes, goals, assists, xG, FPL points, price, opponent.
- `epl_fpl_players_raw` - one row per **player per season**, FPL's own snapshot. It carries `player_code`, the stable ID that survives across seasons.
- `epl_teams` - one row per **team per season**, with FPL's strength ratings.
- `epl_matches` - one row per **match** (380 per season): scores, shots, corners, cards.
- `epl_player_season` - one row per **player per season**, computed from the tables above. The backtest workhorse.

Why keep raw and derived in separate tables? The first four are loaded facts; the fifth is our math. Keeping them apart means the derived table can be dropped and rebuilt any time - you never bake your assumptions into the raw evidence. Same reason accountants keep source documents and working papers in different files.

### 3.3 Running the load

1. Open the **SQL console** (left sidebar of the ClickHouse Cloud console) and start a new query tab.
2. Paste the whole script and hit **Run**.
3. The console executes every statement in sequence: the `SET` line, the `CREATE TABLE`s, the 37 `INSERT`s, the derived-table build, then the sanity `SELECT`s. The output pane shows each statement's result as it goes - the last few print row counts, which are the point (see 3.5).

### 3.4 Reading the script - three excerpts worth understanding

**A table definition** is a list of columns with types, plus how to store them:

```sql
CREATE TABLE IF NOT EXISTS epl_fpl_gameweeks (
  season LowCardinality(String),
  gw UInt8,
  name String,
  ...
) ENGINE = MergeTree ORDER BY (season, player_id, gw);
```

`String` is text, `UInt32` is a whole number, `Nullable(...)` means "allowed to be empty." `MergeTree` is ClickHouse's storage engine, and `ORDER BY` is the sort order it keeps the data in - roughly, the index. Sorting by season, player, gameweek means the questions we actually ask (one player's season, one season's players) read the table in the order it is stored, which is where the speed comes from.

**One load statement** reads almost like English:

```sql
INSERT INTO epl_fpl_gameweeks
SELECT '2024-25' AS season, toUInt8OrZero(GW) AS gw, name, ...
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/gws/merged_gw.csv', CSVWithNames, 'name String, position String, ...');
```

Insert into the table a selection from the CSV at that URL. The long `'name String, position String, ...'` argument tells ClickHouse the CSV's shape; the `toUInt32OrZero(...)`-style functions in the SELECT convert the CSV's text into proper typed numbers. That conversion layer is what "data cleaning" looks like in SQL - a messy real-world file becomes clean typed data in one pass. (If you open the full script you will notice each season's URL argument differs slightly: the source added columns like xG over the years, and the script says so honestly per season.)

**The derived table** is a pivot table in one statement:

```sql
CREATE TABLE IF NOT EXISTS epl_player_season
ENGINE = MergeTree ORDER BY (season, player_id) AS
SELECT g.season, g.player_id, max(r.player_code) AS player_code, ...,
       sum(g.minutes) AS minutes, sum(g.goals_scored) AS goals, sum(g.total_points) AS fpl_points_from_gws, ...
FROM epl_fpl_gameweeks g
LEFT JOIN epl_fpl_players_raw r ON r.season = g.season AND r.player_id = g.player_id
GROUP BY g.season, g.player_id;
```

Group the gameweek rows by player and season, sum the facts, and attach `player_code` from the FPL snapshot via a join (a join stitches two tables together on a shared key). This statement also encodes the project's famous gotcha from the README: the join works **within** a season on `player_id`, but cross-season identity lives in `player_code`, because FPL reissues player IDs every season. The first backtest attempt joined on the wrong key and produced garbage - the data model now carries the fix.

### 3.5 The verification habit: always count rows after a load

A script that runs without errors is not a load that worked. The only proof is counts, so the script ends with three sanity queries: total rows per table, then per-season counts for the gameweek and match tables. What "good" looks like:

- **Matches = exactly 380 per season.** Every EPL season is 20 teams playing 38 rounds - know the shape of your domain so the data has to confess when it is wrong.
- **Gameweek rows in the tens of thousands per season**, growing as the league's data got richer.

The moment a count looks off, something upstream is wrong and you fix it before building on top. This habit - reconcile the totals before you trust the detail - is pure accounting instinct, and it transfers directly.

### 3.6 Try it yourself

1. Run the three sanity queries yourself and compare the per-season match counts to 380.
2. Write one count of your own: `SELECT season, count() FROM epl_fpl_players_raw GROUP BY season ORDER BY season;`
3. Put eyes on raw rows: `SELECT * FROM epl_fpl_gameweeks LIMIT 5;` Analysts who look at raw rows catch things that analysts who only read summaries never do.

