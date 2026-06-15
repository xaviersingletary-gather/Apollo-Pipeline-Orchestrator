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

## What It Does

| Phase | What Happens |
|-------|-------------|
| **Morning Driver (7am)** | Picks top account, researches, finds VP/Director+ contacts, enriches emails, writes bespoke email + call script + LinkedIn note per contact, stages in Apollo, Slack report |
| **Operator Confirm** | Rep reviews, confirms enroll, imports `apollo-import.csv`, activates sequence |
| **Response Watcher (15 min)** | Polls Gmail for replies, classifies (real / OOO / wrong-person), auto-scores real replies, Slacks rep |
| **Weekly Digest** | Friday rollup of runs, enrollments, replies, hopper depth |

---

## Team Onboarding

The fastest way to get running is to let Claude handle the wiring. Paste the repo into a Cowork session, connect your tools, and hand over your account list.

### Fast path (recommended)

**Repo link:** https://github.com/xaviersingletary-gather/Apollo-Pipeline-Orchestrator — copy this and paste it into Claude Cowork.

1. **Open Claude Cowork.** Paste the repo contents into the session.
2. **Connect your stack.** Add Apollo, Slack, Gmail, and Clay as available tools.
3. **Hand Claude your account list.** Paste your target accounts (names, domains, any notes you have).
4. **Tell Claude:**

   > "Set up the Apollo Pipeline Orchestrator for me. Fill my rep identity and Apollo config, score these accounts into a hopper, and register the morning driver and weekly digest scheduled tasks."

5. **One-time Apollo UI step.** Create the four custom fields in Apollo and wire them into your sequence template per `hopper/APOLLO_SETUP.md`. Claude will remind you.
6. **Bank approvals.** Click **Run now** once on the `apollo-morning-driver` task in the Scheduled panel. Approve the tool prompts. Every future run is unattended.

That is it. The next morning Claude starts sourcing contacts, enriching emails, writing content, and Slacking you the staged batch.

### Manual path

If you prefer to run commands yourself or need to debug, the full CLI walkthrough is in `TEAM-SETUP.md`. Most reps never need it.

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
