# Hybrid-by-Quadrant Gate

The decision logic the Morning Driver runs on every account. Implemented in `gate.py` so behavior is identical across daily fires and across teammates. Read this, then use the CLI; do not re-derive the rules by hand.

## The rule

| Verdict | Gate | What happens |
|---|---|---|
| **STRIKE** | `approve` | Prep + stage the CSV, Slack Peter, enroll ONLY after his yes. Protects the no-spam bar on top logos. |
| **NURTURE** | `auto` | Enroll immediately on the morning run. |
| **QUALIFY** | `auto` | Enroll immediately on the morning run. |
| **KILL / IGNORE** | `skip` | Never worked. |

`python3 gate.py gate <VERDICT>` returns `approve | auto | skip`.

## Status lifecycle

`todo -> in_progress -> staged_for_approval -> enrolled -> done | parked`

- **todo**: in the queue, not yet worked.
- **in_progress**: Morning Driver is mid-run on it (set at start so a re-fire doesn't double-work it).
- **staged_for_approval**: STRIKE only. CSV built, waiting on Peter.
- **enrolled**: contacts logged to watcher state; CSV cleared for Apollo upload (or enrolled via Apollo API when connected).
- **parked / done**: out of the active queue.

## L-confidence accounts (needs research)

Ryder and City Furniture scored L confidence. `gate.py` flags them `needs_research`. The Driver must run `account-research` on them FIRST and re-score before enrolling. Do not push thin contacts into outreach.

## Enrollment adapter (Apollo is live)

Apollo MCP is connected. Target sequence + sender + statuses live in `apollo_config.json`
(sequence "Claude Research -> Execution Queue", step 1 = manual email so the bespoke first
touch is rep-sent). The enrollment itself uses Apollo MCP tools, which only run inside a
Claude session (not from gate.py), and Apollo requires explicit human confirmation before
add-to-sequence. So:

- The Driver PREPARES + STAGES (never calls Apollo write tools unattended).
- At Peter's confirm, a Claude session runs the chain: `apollo_contacts_search` (dedupe) ->
  `apollo_contacts_bulk_create` -> `apollo_emailer_campaigns_add_contact_ids` (sequence_id +
  sender from config, status paused for STRIKE / active for auto) -> then
  `python3 gate.py enroll "<account>" "<csv>" --mode apollo --sequence <id>` to RECORD state.
- `--mode csv` remains as a fallback (logs state, flags the CSV for manual upload) if Apollo is down.

## Daily flow the Morning Driver follows

1. `gate.py next` -> get the top todo account + its gate decision + needs_research flag. If empty, fire the low-hopper watchdog (Phase 4).
2. `gate.py set <account> in_progress` (claim it).
3. If `needs_research`: run `account-research`, re-score, continue.
4. Run the pipeline: research -> Clay find/enrich ICP contacts -> personalized email + LinkedIn video script per contact -> write `<date> <Account>/apollo-upload.csv`.
5. Branch on the gate:
   - **approve (STRIKE):** `gate.py stage <account> <csv_path>` -> Slack Peter the summary + CSV. Stop. Enrollment waits for his yes.
   - **auto (NURTURE/QUALIFY):** `gate.py enroll <account> <csv_path> [--sequence ID]` -> contacts logged, CSV cleared.
6. Write the run log to `runs/<date>-<Account>-run.md` and Slack Peter the morning report (Phase 3).

## Peter's approval path (STRIKE)

- `gate.py pending` -> see what's waiting.
- Review the CSV.
- `gate.py approve <account> [--sequence ID]` -> logs contacts to watcher state, marks enrolled, reports the CSV to upload. (Add `--mode apollo` once connected.)

## CLI quick reference

```
gate.py status                       hopper summary + work queue
gate.py next                         next account + gate decision (JSON)
gate.py gate <VERDICT>               approve | auto | skip
gate.py set <account> <status> [--sequence ID] [--worked]
gate.py stage <account> <csv_path>   STRIKE: stage for approval
gate.py pending                      list staged STRIKE runs
gate.py approve <account> [--mode csv|apollo] [--sequence ID]
gate.py enroll <account> <csv_path> [--mode csv|apollo] [--sequence ID]
```
