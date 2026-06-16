# Apollo Pipeline Orchestrator

Self-driving outbound pipeline for Gather AI sales reps. Every weekday morning the system pulls
the top-scored account from a ranked hopper, sources 20 ICP contacts, enriches verified emails,
writes personalized first-touch content per contact, stages them in Apollo, and reports back via
Slack. The human rep only reviews and confirms send.

---

## About

This project codifies the entire outbound motion — scoring, sourcing, enrichment, content
generation, staging, and response handling — into a portable toolkit. The philosophy: automate
everything that does not require human judgment, gate everything that does. Nothing ships
without an explicit confirm and activate. The rep stays the human on the calls, the LinkedIn
videos, and the send button — the system handles the prep.

All scoring rules, voice rules, and cadence logic are in files, not in anyone's head. Clone the
repo, run setup, fill your identity, and you are live.

Built by Peter Tosh at Gather AI, June 2026.

---

## How It Works

1. **Monday morning pick.** The system locks the top-scored account from your ranked hopper.
2. **Research.** It reads the account domain, news, and any notes you have on the company.
3. **Find 20 contacts.** Clay sources VP/Director+ ICP contacts with verified work emails.
4. **Write personalized content.** Every contact gets a bespoke email, call script, and LinkedIn note based on their role and the account's context.
5. **Stage in Apollo.** Contacts are loaded into a sequence with custom fields populated via CSV.
6. **Slack report.** You get a DM with the batch summary, ready for review.
7. **Rep reviews and confirms.** You check the work, hit enroll, and activate. The Response Watcher polls Gmail for replies, classifies them, and Slacks you the results. Friday brings a Weekly Digest rollup.

---

## Team Onboarding

The fastest way to get running is to let Claude handle the wiring. Add this repo to Cowork context, connect your tools, and send one command.

**Repo:** https://github.com/xaviersingletary-gather/Apollo-Pipeline-Orchestrator

### PRE-FLIGHT CHECKLIST

Do not skip these. The setup will fail without them.

- [ ] **Apollo account with a connected Gmail mailbox** (hard prerequisite — sequences send from this mailbox)
- [ ] **Cowork connected to:** Apollo, Slack, Gmail, Clay
- [ ] **Target account list ready** (company names, domains, any notes)
- [ ] **20–30 minutes free** (you will be approving tool prompts)

### Fast path (recommended)

⏱ **Time expectation: 15–30 minutes.** Most of it is waiting and clicking "Always allow."

1. **Connect your apps.** In Cowork settings, add Apollo, Slack, Gmail, and Clay as available tools.
2. **Add the repo to Cowork context.** Paste the repo link above into the session **and add it to Cowork context** — do not just drop a link in chat. You can also drag the local folder into the session.
3. **Send one command:**

   > `run apollo setup`

4. **Wait and approve.** Claude will scaffold your workspace and hydrate your configs. Click **Always allow** on every tool prompt. After setup finishes, go to the Scheduled panel, click **Run now** once on `apollo-morning-driver`, and **Always allow** again. This banks every approval needed for unattended morning runs — future runs need zero interaction.
5. **One-time Apollo UI step.** Wire the four Gather custom fields into your sequence template.
   
   This is the only manual UI step. It takes 5 minutes and you do it once.
   
   Open Apollo → **Engage** → **Sequences** → open YOUR target sequence → **Steps** tab.
   
   - **Day-1 email:** Edit Step 1 → Subject field → click the **{ }** button → select `Gather_Email_Subject`. Body field → delete all text → click **{ }** → select `Gather_Email_Body` (leave ONLY this token). Save.
   - **Call steps (Day 1, 3, 8):** Edit each → Notes field → click **{ }** → select `Gather_Script`. Save.
   - **LinkedIn connection (Day 1):** Edit → Message field → click **{ }** → select `Gather_Connection_Note`. Save.
   
   **Never hand-type the tokens.** Always use the `{ }` picker or emails ship as literal text.
   
   Full visual walkthrough with screenshots: `hopper/APOLLO_SETUP.md`

That is it. The next morning Claude starts sourcing contacts, enriching emails, writing content, and Slacking you the staged batch.

---

## What It Does

| Phase | What Happens |
|-------|-------------|
| **Morning Driver (7am)** | Picks top account, researches, finds VP/Director+ contacts, enriches emails, writes bespoke email + call script + LinkedIn note per contact, stages in Apollo, Slack report |
| **Operator Confirm** | Rep reviews, confirms enroll, imports `apollo-import.csv`, activates sequence |
| **Response Watcher (15 min)** | Polls Gmail for replies, classifies (real / OOO / wrong-person), auto-scores real replies, Slacks rep |
| **Weekly Digest** | Friday rollup of runs, enrollments, replies, hopper depth |

---

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Scheduler  │────▶│ Morning Driver  │────▶│    Clay      │
│  (cron 7am) │     │ (Claude session)│     │(find/enrich) │
└─────────────┘     └─────────────────┘     └──────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐          ┌──────────────┐
                       │ hopper.json │          │   Apollo     │
                       │  (queue)    │          │ (stage/load) │
                       └─────────────┘          └──────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐          ┌──────────────┐
                       │  Slack DM   │◄─────────│ Operator     │
                       │  (report)   │          │ (review/send)│
                       └─────────────┘          └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Response Watcher (15 min)                 │
│  Gmail poll → classify → real: score+handoff | ooo: notify │
└─────────────────────────────────────────────────────────────┘
```

---

## Scoring Hopper

Accounts are ranked on a Fit x Signal matrix (4 fit dimensions, 5 signal dimensions). Verdicts:

| Verdict | Criteria | Handling |
|---------|----------|----------|
| STRIKE | Fit >=70, Signal >=70 | Prep + stage, you review before send |
| NURTURE | Fit >=70, Signal <70 | Pre-trusted, one-tap enroll |
| QUALIFY | Fit 40-69, Signal >=40 | Pre-trusted, one-tap enroll |
| KILL | Either <40 | Never worked, off queue |

---

## Project Structure

```
Apollo Pipeline Orchestrator/
├── hopper/                          # Core pipeline engine
│   ├── gate.py                      # Queue + gate logic (next, stage, enroll)
│   ├── digest.py                    # Weekly rollup generator
│   ├── build_hopper.py              # Fit x Signal scoring + hopper builder
│   ├── setup.py                     # Scaffolds workspace + hydrates configs
│   ├── MORNING_DRIVER.md            # Daily driver prompt template
│   ├── GATE.md                      # Hybrid gate rules by quadrant
│   ├── APOLLO_SETUP.md              # One-time Apollo custom-field wiring
│   ├── apollo_config.template.json  # Template for Apollo wiring
│   ├── rep_config.template.json     # Template for rep identity
│   ├── apollo_config.json           # YOUR Apollo config (generated from template)
│   ├── rep_config.json              # YOUR identity (generated from template)
│   └── hopper.jsonl                 # YOUR ranked account queue
│
├── state/                           # Runtime state (response watcher)
│   ├── active-contacts.jsonl        # Contacts enrolled in sequences
│   ├── processed-replies.jsonl      # Reply deduplication log
│   └── pending-approvals.jsonl      # Accounts staged awaiting operator
│
├── runs/                            # Per-run audit logs
│   └── YYYY-MM-DD-<Account>-run.md
│
├── apollo-onboard-skill/            # Skill: "run apollo setup"
├── gather-apollo-pipeline-skill/    # Skill: morning driver
├── gather-apollo-response-watcher-skill/  # Skill: reply watcher
├── build_deck.py                    # Team setup deck generator
├── TEAM-SETUP.md                    # Full setup instructions
├── TECHNICAL-SPEC.md                # Node-by-node process spec
├── TRACKER.md                       # Build tracker / component status
└── README.md                        # This file
```

---

## Key Dependencies

- **Claude / Cowork** — orchestrator, scheduled tasks, tool calls
- **Apollo** — contact database, sequences, sending
- **Clay** — ICP contact find + email enrichment
- **Gmail** — outbound sending + reply ingestion
- **Slack** — rep notifications + reports

---

## Safety Invariants

- Nothing sends without explicit human confirm (enroll + activate gates)
- Account locked before work, released on any exit
- All tool approvals banked once via "Run now"; unattended runs need no interaction
- Apollo custom fields populate via CSV import before activation (prevents blank sends)
- Response watcher deduplicates via `processed-replies.jsonl`

---

## Status

- 11+ accounts scored across patches
- DHL end-to-end run completed (6 contacts sourced, enriched, written, loaded)
- Daily driver + weekly digest live and scheduled
- Response watcher packaged, awaiting first dry-run
- Repo cleaned for team cloning — no PII or machine-specific paths committed

Port to any rep's patch by cloning, running setup, and filling identity.

---

## Manual path (if you prefer CLI)

If you prefer to run commands yourself or need to debug, the full CLI walkthrough is in `TEAM-SETUP.md`. Most reps never need it.
