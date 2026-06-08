# Self-Driving Apollo Pipeline — Technical Process Spec (for IT)

Authoritative, node-by-node description of what runs, which tool is called, the inputs, the
success test, the retry/failure behavior, and what data is written. Node IDs (N0..N18) match the
diagram in `apollo-pipeline-flow.mmd` / `process-map.html`.

## Actors / systems
- **Operator** — the sales rep. Human.
- **Scheduler** — Cowork scheduled-tasks service (cron). Fires the driver.
- **Claude (orchestrator)** — the agent session that executes the driver prompt; runs Bash + MCP calls.
- **gate.py / digest.py** — local Python in `hopper/`. Pure state logic; no network, no MCP.
- **Clay (MCP)** — server `08e80527...`: `find-and-enrich-contacts-at-company`, `add-contact-data-points`, `get-task-context`.
- **Apollo (MCP)** — server `56a457ca...`: `apollo_emailer_campaigns_search`, `apollo_email_accounts_index`, `apollo_contacts_search`, `apollo_contacts_bulk_create`, `apollo_emailer_campaigns_add_contact_ids`, `apollo_emailer_campaigns_approve`.
- **Slack (MCP)** — `slack_send_message`, `slack_search_users`.
- **Gmail (MCP)** — `search_threads`, `get_thread`, `create_draft` (used by the response watcher).

## State files (local, in the orchestrator folder)
- `hopper/hopper.jsonl` — one JSON object per account. Fields: rank, account, domain, verdict, fit, signal, confidence, top_move, status, last_worked_at, sequence_target, scored_at. status in {todo, in_progress, staged_for_approval, enrolled, parked, done}.
- `hopper/apollo_config.json` — shared sequence id, sender mailbox id, custom-field names, import-csv schema, daily target, ICP titles.
- `hopper/rep_config.json` — rep identity (name, email, title, phone, signature, slack_user_id, mailbox id, about-me path).
- `state/active-contacts.jsonl` — every enrolled contact (for the response watcher).
- `state/processed-replies.jsonl` — replies already handled (dedupe).
- `state/pending-approvals.jsonl` — STRIKE accounts staged, awaiting operator yes.
- `runs/<date>-<account>-run.md` — per-run audit log.

---

## PUSH SIDE — the morning driver (scheduled, weekday 07:04 local)

### N0 — Scheduler fires
Trigger: cron `3 7 * * 1-5` on the durable task `apollo-morning-driver`. Spawns a fresh Claude
session with the self-contained driver prompt (`hopper/MORNING_DRIVER.md`). No memory of prior runs.
Tool approvals were pre-granted by the operator's one-time "Run now". If not granted, the session
stalls on first tool call (documented failure mode F1).

### N1 — Pick next account
Actor: Claude -> Bash `python3 hopper/gate.py next`.
Logic: read hopper.jsonl, return the top-ranked row with status=todo as JSON
(account, domain, verdict, gate, needs_research, remaining_todo, top_move).
gate mapping: STRIKE->approve, NURTURE/QUALIFY->auto, KILL->skip.
Branches:
- `{"empty": true}` and >=1 account already worked this run -> go to N16 (report).
- `{"empty": true}` and nothing worked -> N15 (Slack "hopper empty") then end.
- gate==skip -> `gate.py set <account> parked`, loop back to N1.

### N2 — Claim account (idempotency lock)
Actor: Claude -> Bash `gate.py set "<account>" in_progress`.
Purpose: prevents a re-fire or parallel run from double-working the same account. Any abnormal
exit must reset this to todo (see F-series).

### N3 — Research
Actor: Claude. Decision: does a research file < 14 days old exist on disk for this account?
- If needs_research==true (confidence L) OR no fresh file -> invoke `account-research` skill, wait
  for completion, then read the produced research file.
- Else read the existing file.
Output extracted: sub-org map, trigger events (<=90 days), the specific operational pain. These are
inputs to N7 (content).

### N4 — Source ICP contacts (Clay), PASS 1
Actor: Claude -> Clay `find-and-enrich-contacts-at-company`.
Inputs: companyIdentifier=<domain>; contactFilters.job_title_keywords = apollo_config.icp_titles
(VP/SVP + Director/Sr Director of Operations, Supply Chain, Logistics, Distribution, Fulfillment;
DC Ops directors; warehouse/DC GMs); contactFilters.locations=["United States"].
Returns: a batch of candidate contacts (name, title, linkedin, profile_id/entityId, domain).

### N5 — Filter to qualified ICP
Actor: Claude (in-session logic). Keep only: title is Director level or above; company domain
matches the target (drop wrong-company hits); drop non-director Managers, engineers, recruiters,
sustainability/tech roles, duplicates. Produces the candidate set to enrich.

### N6 — Enrich + validate contact data (Clay), with poll loop
Actor: Claude -> Clay `add-contact-data-points` (dataPoints=[Email]) on the filtered entityIds,
then Clay `get-task-context` to read results (enrichment is async).
Poll: call `get-task-context` until each contact's Email enrichment state == "completed" (or
"error").
VALIDITY GATE (current): keep a contact only if it has a verified email (email_status=verified).
Optional stricter gate (toggle `require_phone` in apollo_config, default off): also require >=1
valid phone; phone comes from the Apollo contact record at N9, so enabling it moves the phone check
to after N9 and drops contacts lacking a number.
Count valid contacts for this account this run.

### N6-RETRY — sourcing retry loop (max 3 passes per account)
If valid count < 20 after a pass:
- Pass 2: re-call N4 with the NEXT page (pagination, per_page up to 100) and/or a broadened title
  set, then N5, N6 again.
- Pass 3: same, once more.
- Hard cap: 3 sourcing passes per account. (This is the formalization of "poll Clay up to twice
  more until 20 valid contacts are met.")
After 3 passes:
- If >0 but <20 and account is genuinely exhausted (small account) -> proceed with what qualifies,
  and after staging (N12) loop back to N1 to top the DAY up toward 20 from the next account.
- If 0 valid -> N15a (Slack "ICP returned nothing for <account>"), `gate.py set <account> todo`,
  loop to N1 (do not kill the whole run).
Per-account cap: never take more than 20 from one account.

### N7 — Generate first-touch content (per contact)
Actor: Claude, governed by `ABOUT ME/about-me.md` + `anti-ai-writing-style.md`. For each valid
contact, produce: email subject, email body, a 30-45s script (call opener + LinkedIn video), and a
<300-char LinkedIn connection note. Anchored to N3 triggers. Voice guard: reject em dashes / AI-tell
vocabulary and rewrite before saving. No invented dollar figures.

### N8 — Write CSVs
Actor: Claude -> writes two files in `runs`-adjacent `<date> <Account>/`:
- `apollo-upload.csv` (human run record): first_name,last_name,email,title,company,linkedin_url,location,persona_tag,priority_tier,email_subject,email_body,linkedin_video_script
- `apollo-import.csv` (Apollo import-ready, headers = custom fields): email,first_name,last_name,title,company,linkedin_url,Gather_Email_Subject,Gather_Email_Body,Gather_Script,Gather_Connection_Note

### N9 — Create contacts in Apollo (dedupe)
Actor: Claude -> Apollo `apollo_contacts_search` (by email) to detect existing; then
`apollo_contacts_bulk_create` (or per-contact `apollo_contacts_create` with run_dedupe=true) for new
ones. Captures each contact's 24-char Apollo id. Tags with labels (e.g. account name). NOTE: this
writes to Apollo but does NOT enroll or send.

### N10 — Quadrant gate decision
Actor: Claude reads gate from N1.
- gate==approve (STRIKE) -> N11 (stage for human approval). DO NOT enroll.
- gate==auto (NURTURE/QUALIFY) -> still stage in the unattended run (Apollo enrollment requires a
  human confirm and must not run unattended). Enrollment for both tiers happens at N13 after the
  operator confirms; the gate only changes the Slack ask (review-then-confirm vs just-confirm).

### N11 — Stage
Actor: Claude -> Bash `gate.py stage "<account>" "<apollo-upload.csv>"`.
Effect: hopper row status -> staged_for_approval; appends a record to state/pending-approvals.jsonl
(account, verdict, csv_path, contact count, timestamp).

### N12 — Run log
Actor: Claude -> writes `runs/<date>-<Account>-run.md` (steps, counts sourced/enriched/in-CSV, gate,
csv paths, any skips/failures).

### N16 — Morning Slack report (always, once per run)
Actor: Claude -> Slack `slack_send_message` to rep_config.slack_user_id. One message covering all
accounts worked: per-account counts + gate, total vs 20 target, queue depth (with REPLENISH flag if
todo < 3), confirm-enroll instruction, paths. This is the only step the operator sees.

---

## OPERATOR CONFIRM -> ENROLL (interactive, later in the day)

### N13 — Operator confirms enroll
Trigger: operator replies "enroll <account>" (STRIKE: after reviewing content; auto: rubber stamp).
Actor: Claude (interactive session) -> Apollo, in order:
1. `apollo_emailer_campaigns_search` (confirm shared sequence id from apollo_config).
2. `apollo_email_accounts_index` (confirm rep's sender mailbox id).
3. `apollo_emailer_campaigns_add_contact_ids`: id+emailer_campaign_id=shared sequence,
   send_email_from_email_account_id=rep mailbox, contact_ids=N9 ids, status=paused (STRIKE) or
   active (auto). Apollo enforces explicit human confirmation here.
Then Bash `gate.py enroll "<account>" "<csv>" --mode apollo --sequence <id>`: hopper status ->
enrolled; appends each contact to state/active-contacts.jsonl (for the watcher).

### N14 — Import per-contact content + activate (operator, Apollo UI)
Operator imports `apollo-import.csv` (match on Email -> maps Gather_* columns to the custom fields
the admin created once). Then activates/unpauses the sequence. Day-1 email is a manual_email step;
the operator sends it. GUARD: do not activate before the import populates fields, or a blank/literal
template sends.

---

## PULL SIDE — response watcher (separate scheduled task, every 15 min)

### N17 — Poll Gmail for replies
Actor: scheduled `gather-apollo-response-watcher` -> reads state/active-contacts.jsonl, for each
contact email calls Gmail `search_threads` (from:contact, last ~24h overlap window) -> `get_thread`
for the latest message. Skips message_ids already in state/processed-replies.jsonl.

### N18 — Classify + route
Actor: Claude classifier (in-session, pattern-based). real / out-of-office / wrong-person.
- real -> invoke `lead-scoring-and-handoff` (produces handover doc) -> Slack the rep score + link.
- ooo / wrong-person -> Slack the rep the text with a "needs guidance" tag, no scoring.
Always append to processed-replies.jsonl (dedupe). Bias ambiguous -> real.

---

## Failure modes (explicit)
- F1 Tool not pre-approved: unattended session stalls. Cause: "Run now" never done. Mitigation: one-time operator action; documented in setup.
- F2 Clay returns 0 after 3 passes: Slack notice, account back to todo, continue run. No crash.
- F3 Enrichment stuck "in-progress": poll get-task-context with bounded retries; drop contacts that never resolve; proceed with the rest.
- F4 Apollo field IDs unavailable to API (non-master key): per-contact fields cannot be written by API; the CSV import (N14) is the supported path. Documented limit.
- F5 Any step throws: Slack the one-line failure, `gate.py set <account> todo` (release the lock), write run log, exit cleanly. Never leave status=in_progress.
- F6 Sequence missing/paused at enroll: Apollo returns error; Claude surfaces it, does not retry blindly.

## Idempotency & safety invariants
- An account is locked (in_progress) before work and released on any exit.
- Nothing sends without an explicit human confirm (N13) and activate (N14); the unattended driver never calls add_contact_ids or approve.
- All Apollo/Slack IDs must come from a live tool call in-session; never fabricated.
- processed-replies.jsonl + active-contacts.jsonl make the watcher idempotent across 15-min runs.
