# Learn With Me: How This Project Gets Built

This file is the beginner's companion to the project. Every time the project hits a new milestone, a new chapter lands here explaining what we did - and, just as important, why we did it that way - with the exact steps, so that by the end you could build something like it yourself.

No prior experience assumed. Jargon gets explained the first time it appears. If you know what an Excel pivot table is, you know enough to follow along.

## Chapters

1. **From zero to a GitHub repo** (this chapter)
2. ClickHouse Cloud: your account and your first service - *coming as we build*
3. Loading data with the `url()` table function - *coming as we build*
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

