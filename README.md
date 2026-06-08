# Apollo Pipeline Orchestrator

Self-driving outbound pipeline for Gather AI sales reps. Every weekday morning the system pulls the top-scored account from a ranked hopper, sources 20 ICP contacts, enriches verified emails, writes personalized first-touch content per contact, stages them in Apollo, and reports back via Slack. The human rep only reviews and confirms send.

---

## What It Does

| Phase | What Happens |
|-------|-------------|
| **Morning Driver (7am)** | Picks top account from scored hopper, researches, finds VP/Director+ contacts, enriches emails, writes bespoke email + call script + LinkedIn note per contact, stages in Apollo, Slack report |
| **Operator Confirm** | Rep reviews staged account, confirms enroll, imports per-contact content via CSV, activates sequence |
| **Response Watcher (15 min)** | Polls Gmail for replies from active contacts, classifies (real / OOO / wrong-person), auto-scores real replies and Slacks rep |
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
│   ├── setup.py                     # One-command workspace scaffold
│   ├── MORNING_DRIVER.md            # The daily driver prompt (scheduled task)
│   ├── GATE.md                      # Hybrid gate rules by quadrant
│   ├── APOLLO_SETUP.md              # One-time Apollo custom-field wiring
│   ├── apollo_config.json           # Shared Apollo wiring (sequence, fields)
│   ├── rep_config.template.json     # Template for per-rep identity
│   └── hopper.jsonl                 # Machine queue (generated per rep)
│
├── state/                           # Runtime state (response watcher)
│   ├── active-contacts.jsonl        # Contacts enrolled in sequences
│   ├── processed-replies.jsonl      # Reply deduplication log
│   └── pending-approvals.jsonl      # Accounts staged awaiting operator
│
├── runs/                            # Per-run audit logs
│   └── YYYY-MM-DD-<Account>-run.md
│
├── apollo-onboard-skill/            # "run apollo setup" skill
│   └── SKILL.md
│
├── gather-apollo-pipeline-skill/    # Morning driver skill
│   └── SKILL.md
│
├── gather-apollo-response-watcher-skill/  # Reply watcher skill
│   ├── SKILL.md
│   └── references/classifier-patterns.md
│
├── gather-apollo-pipeline.skill     # Packaged pipeline skill
├── gather-apollo-response-watcher.skill   # Packaged watcher skill
├── build_deck.py                    # Team setup deck generator
├── Apollo-Pipeline-Team-Setup-Guide.pptx   # Setup deck
├── Apollo-System-Presentation-Brief.md   # Slide-by-slide deck brief
├── TEAM-SETUP.md                    # Written setup instructions
├── TECHNICAL-SPEC.md                # Node-by-node process spec
├── TRACKER.md                       # Build tracker / component status
└── README.md                        # This file
```

---

## Quick Start

1. Install the onboard skill: copy `apollo-onboard-skill/` into your Cowork skill directory.
2. Type: `run apollo setup`
3. Follow the prompts (paste accounts, create Apollo custom fields, click "Run now" once).
4. The 7am driver works your patch from there.

Full written steps: see `TEAM-SETUP.md`

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

- 11 accounts scored (3 STRIKE, 6 NURTURE, 2 QUALIFY)
- DHL end-to-end run completed (6 contacts sourced, enriched, written, loaded)
- Daily driver + weekly digest live and scheduled
- Response watcher packaged, awaiting first dry-run

Built by Peter Tosh at Gather AI. Port to any rep's patch by copying the folder and running setup.
