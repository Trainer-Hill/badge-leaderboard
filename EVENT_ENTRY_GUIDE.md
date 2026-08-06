# How to Add an Event to the Badge Leaderboard

This is the guide for entering tournament results into the Area Zero badge leaderboard.
It covers adding events only — everything else (rules, season setup, deck icons) is handled
separately.

If something in here doesn't match what you see on screen, ping Brad — the form changes
occasionally.

---

## 1. Getting in

1. Go to **https://badges.areazerotcg.com/admin/event**

   There is no link to this page in the site navigation — you have to type the URL (or
   bookmark it). The public site lives at `badges.areazerotcg.com`; the `/admin/event`
   path is the entry form.

2. Your browser will pop up a login prompt. Enter the **username and password Brad gave
   you**. This is standard browser Basic Auth, so your browser will usually offer to
   remember it.

   > 📸 *[SCREENSHOT: browser login prompt]*

3. Once you're in, you'll see the **Enter Event** page, with the current season in the
   heading (e.g. "Enter Event — 2027 Season").

   > 📸 *[SCREENSHOT: full event entry page, freshly loaded]*

**Notes on logging in**

- Everyone with an account is an admin — there are no partial permissions. Please only
  add events you actually have results for.
- Whoever is logged in gets stamped on the event as its author. This is only for
  our own record-keeping and never shows up on the public site.
- If the login prompt keeps reappearing, the credentials are wrong. Don't guess a bunch
  of times — just ask.

---

## 2. Event details (the top section)

> 📸 *[SCREENSHOT: the event details row — Store, Date, Total Players, Tier, Format]*

| Field | What to put |
|---|---|
| **Store** | Pick from the dropdown if the store is already listed. If it's a new venue, type the name into the box below the dropdown and hit the **+** button to add it. Try to match the existing spelling exactly so the store doesn't show up twice on the site. |
| **Date** | The date the event was played, not the date you're entering it. Defaults to today. |
| **Total Players** | Attendance **in the primary division** — see the section below. This drives a lot. |
| **Tier** | Locals, Online, League Challenge, League Cup, Regionals, Internationals, or Worlds. |
| **Format** | Usually Standard. Same select-or-add-new pattern as Store. |

### About Total Players

This is the field people most often skip, and it does the most work. Fill it in.

**Use the player count of the primary division only — usually Masters.** Not the combined
attendance across divisions. When an event runs divisions combined, still count only the
primary division.

The reason: the number of Swiss rounds is set by the primary division's size, and the badge
cutoffs are built around round count. Using combined attendance inflates the number and
hands out badges too deep.

### Combined vs. separate divisions

**One tournament = one event.** If a small number of Seniors or Juniors got grouped in with
Masters and played a single tournament, that's *one* event with everyone in the standings —
use the primary division's attendance for the player count.

Only enter separate events when the divisions actually ran as **separate tournaments** with
their own pairings and standings, as at a large Regional.

This is where the undefeated rule really matters. Say a local has **12 Masters and 2
Seniors** playing combined. Twelve players means the table below awards one badge — 1st
place. But the tournament software pairs everyone together, so a Senior can finish 4-0 and
land in 2nd behind a 4-0 Master. **That Senior still earns a badge**, because anyone who
wins all their matches earns one regardless of placement. Toggle it on manually.

When you enter a player count, the form will:

1. **Tell you who earns a badge.** The cutoff scales with attendance:

   | Attendance | Badge goes to |
   |---|---|
   | Up to 16 | 1st place only |
   | 17–32 | Top 2 |
   | 33–64 | Top 4 |
   | 65+ | Top 8 |

2. **Auto-create standings rows for you**, pre-filled with placements and with the Badge
   toggle already flipped on for whoever earned one. It suggests recording roughly
   "everyone at one loss or better" — so a 5-round event suggests recording down to 4-1.

3. **Show a hint line** above the standings, e.g.
   *"Top 2 earn a badge. Record ~6 — anyone at 4-1 or better (one loss)."*

   > 📸 *[SCREENSHOT: the badge hint line under "Standings"]*

**Important things about the auto-generated rows:**

- The suggested count is a *starting point*, not a rule. Add more rows with **Add Player**
  if you want to record deeper.
- For **65+ player events**, the badge cutoff caps at Top 8. If there are ties with 8th
  place's record, or the cut was asymmetrical, that's a manual judgment call — flip the
  Badge toggle on yourself for those players.
- **Anyone who went undefeated earns a badge**, even if they placed below the cutoff. The
  form won't catch this — toggle it on manually. (And for 3-round events, an undefeated
  record is the *only* way to earn one.)

### If the event had a top cut

When an event runs a single-elimination top cut, **record the whole cut** — we'd like to
see the full Top 8 (or Top 4) in the standings even though the lower seeds may have two
losses and fall below the "one loss or better" suggestion. The hint line will flag this
when the likely cut runs deeper than the suggested count. Typical cuts: under 13 players
usually no cut, 13–20 is a Top 4, 21+ is a Top 8.

**Making cut does not earn a badge.** Recording the cut is about having complete, useful
standings — badges still follow the attendance table above. So at a 40-player event with a
Top 8, you'd record all eight players but only the Top 4 get the Badge toggle.

---

## 3. Adding decks

> 📸 *[SCREENSHOT: the "Add a deck" section — icons dropdown and deck name box]*

Decks that have been used before are already in the per-player Deck dropdown. If a deck
you need isn't there yet, build it in the **Add a deck** section *before* filling in the
standings:

1. Pick the Pokémon icons from the **Icons** dropdown (you can select more than one — type
   to search).
2. Type the deck name into the box.
3. Hit the **+** button. The deck now appears in every player's Deck dropdown on the page.

### Which name to use

**Use the deck name recorded at https://play.limitlesstcg.com/decks.** That's our source of
truth so names stay consistent across events and the deck leaderboard doesn't fragment into
three spellings of the same thing.

> 📸 *[SCREENSHOT: play.limitlesstcg.com/decks page showing deck names]*

### When the icon doesn't exist yet

Occasionally a Pokémon hasn't shown up in the icon dropdown yet. This happens with **newly
released Pokémon** — Mega Evolutions have been the recent case, but any new Pokémon can hit
it, and there's another batch landing in a few months. The sprite data we pull from lags
behind the set release. Anything that's been out a while is already there.

**If you can't find the icon you need, message Brad before creating the deck.** Updating the
sprite data is on his side, not something you can fix from the form. He'll either tell you
to hold the event until the icon lands, or to go ahead with substitute icons for now — it
depends on how far out the fix is.

Default to waiting. It's much easier than fixing up badges after the fact. And don't invent
a slightly-different deck name to work around a missing icon.

---

## 4. Standings

Each player gets a row.

> 📸 *[SCREENSHOT: a couple of standings rows, one with the Badge toggle on and its extra fields showing]*

**Every row has:**

- **Placement** — final standing (1, 2, 3…). Pre-filled when rows are auto-created.
- **Trainer** — pick from the dropdown if they've been recorded before. For a new player,
  type their name in the "New trainer" box underneath and hit **+**.
- **Deck** — from the dropdown (see the deck section above).
- **Badge toggle** — on if this player earned a badge. Pre-set from placement + attendance,
  but you can override it.
- **Trash icon** — removes the row.

**Rows with the Badge toggle ON also show:**

- **Pronouns** — `their` / `her` / `his`. **If you're not sure, use `their`.** It's the
  default and it's never wrong. Don't guess based on a name.
- **Color** — the badge's accent color. Pick something the player likes, or match what
  they've had before.
- **Background** — an energy type (Grass, Fire, Water, Lightning, Psychic, Fighting, Dark,
  Metal, Dragon, Fairy, Colorless). Usually matches their deck.
- **Discord ID** — only shows when we don't already have one for that trainer (see below).

Pronouns, color, background, and Discord pings are **only collected for badge earners**.
Non-earners are recorded as standings data only — placement, trainer, deck.

### Things that fill in automatically

- **Pronouns** auto-fill from the most recent badge we have for that trainer as soon as you
  pick them from the dropdown. If it fills in, leave it alone — don't override it unless
  the player has told you otherwise.
- **Discord ID**: if we already have one on file for that trainer, the input disappears and
  you'll see a green ✅ *"Ping ready for this trainer"* instead. Nothing to do.

  > 📸 *[SCREENSHOT: row showing the green "Ping ready for this trainer" indicator]*

### Major events work differently

At a **major event** — Regionals, Special Events, Internationals, Worlds — a player earns a
badge by **advancing to Phase Two**, regardless of where they finish. They don't have to
place in the Top 8.

The form doesn't know this. It'll pre-set Badge toggles from placement like it does for
everything else, so for majors you'll need to go in and **toggle Badge on for everyone who
made Phase Two**, and add rows for them with **Add Player** since the auto-generated rows
won't go nearly deep enough. Set each player's placement to their actual final standing.

Majors are also where divisions genuinely run as separate tournaments, so a Regional's
Masters and Seniors standings go in as two entries, each with its own player count.

### Blank rows are ignored

**If a standings row has no trainer selected, it's silently skipped when you save.** So if
the form generated 8 rows and you only have results for 5, just leave the last three empty
— no need to delete them. (Deleting them is fine too, it just isn't necessary.)

---

## 5. How to get someone's Discord ID

We store Discord IDs so the bot can @-mention people when their badge is announced. You
only need to do this **once per player** — after that the field won't even appear.

To get an ID:

1. In Discord, open **User Settings → Advanced** and turn on **Developer Mode**.

   > 📸 *[SCREENSHOT: Discord Developer Mode toggle]*

2. Right-click the person's username or avatar anywhere in the server.
3. Choose **Copy User ID**.

   > 📸 *[SCREENSHOT: Discord right-click menu with "Copy User ID"]*

4. Paste it into the Discord ID box on their standings row. It's a long number, something
   like `123456789012345678` — no `@`, no `#1234`, no display name.

On mobile: long-press the user's avatar → **Copy User ID** (Developer Mode still needs to
be on, under Settings → Advanced).

If you can't get an ID, leave it blank — the badge still saves, they just get named in the
announcement instead of pinged, and we can add the ID later.

---

## 6. Saving

Hit **Save Event** at the bottom. You'll be sent back to the leaderboard homepage.

> 📸 *[SCREENSHOT: Save Event button]*

**Give it a moment.** The page may sit there for a few seconds after you click — the server
is recalculating the leaderboard and firing off the Discord pings. Don't click Save again;
you'll risk entering the event twice. Wait until you land back on the homepage.

On save:

- The event and all its standings are recorded.
- **A Discord announcement is posted for every badge earner** in the event. This is
  immediate and public, so double-check names, decks, and badge toggles before you hit
  save.
- Any new Discord IDs you entered are saved for next time.

**Store and Date are required.** You'll also get an error if every row is blank.

---

## 7. Fixing a mistake

At the top of the page there's an **Edit existing event** dropdown, listing events as
`Store — Date — 42p`.

> 📸 *[SCREENSHOT: Edit existing event dropdown, expanded]*

Pick the event and the whole form loads with its saved values. Fix what's wrong and hit
**Update Event**.

Worth knowing:

- **Editing does not re-post to Discord.** No duplicate announcements — but also no new
  announcement if you add a badge earner during an edit. Let people know manually in that
  case.
- While editing, the standings load exactly as saved and changing Total Players will
  **not** generate new rows. Use **Add Player** if you need more.
- Clearing the dropdown resets the form to a blank new event.
- Adding the same event twice creates a duplicate — check the edit dropdown first if
  you're unsure whether it's already in.

---

## Quick checklist

- [ ] Logged in at `badges.areazerotcg.com/admin/event`
- [ ] Store, Date, **Total Players (primary division only)**, Tier, Format filled in
- [ ] One event per *tournament* — combined divisions stay in one event
- [ ] Deck names match play.limitlesstcg.com/decks
- [ ] Standings entered down to roughly the suggested depth, plus the full top cut if there was one
- [ ] Badge toggles match the attendance cutoff — manually adjusted for undefeated players, ties at large events, and Phase Two at majors
- [ ] Pronouns for badge earners (`their` if unsure)
- [ ] Color + background set for badge earners
- [ ] Discord IDs added for anyone new
- [ ] Reviewed before saving — Discord pings fire immediately
- [ ] Waited for the save to finish instead of double-clicking

---

## Questions / problems

Ping Brad. Specifically for:

- Missing Pokémon icons (especially Mega Evolutions)
- Credentials not working
- An event that saved wrong and won't edit cleanly
- Anything in this doc that doesn't match the site
