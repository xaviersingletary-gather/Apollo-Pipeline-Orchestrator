---
name: apollo-onboard
description: >
  One-command onboarding for the Self-Driving Apollo Pipeline. Stands up the whole system for a
  new rep: scaffolds the workspace, discovers their Slack and Apollo IDs, writes their config,
  scores their accounts into the hopper, and registers the morning driver + weekly digest
  scheduled tasks. Pauses only for the human-only steps (the rep's account list, creating Apollo
  custom fields in the UI, and the one-time "Run now" approval). Use this skill whenever the rep
  says "run apollo setup", "run setup", "set up my apollo pipeline", "onboard me to the apollo
  pipeline", "set up the self-driving pipeline", or any request to install/stand up this system
  for themselves. Do not use for a daily run (that is the apollo-morning-driver scheduled task).
---

# Apollo Pipeline — One-Command Onboarding

You are setting up the Self-Driving Apollo Pipeline for a new rep who just typed the trigger.
Do every step you can automatically. Stop and ask only where a human must act. Be brisk; this
should feel like one flow, not an interview. Confirm each milestone in one line.

## Step 0 — Locate the toolkit
Find the orchestrator folder: search the user's OUTPUTS for `Apollo Pipeline Orchestrator/hopper/gate.py`.
Set BASE = that folder. If you cannot find it, tell the rep to copy the "Apollo Pipeline
Orchestrator" folder into their Cowork OUTPUTS first, then re-run. All paths below are under BASE.

## Step 1 — Scaffold (automatic)
Run: `python3 "$BASE/hopper/setup.py"`. This creates state/, runs/, an empty hopper, and
rep_config.json. Report the one-line result.

## Step 2 — Identity (automatic, with one quick ask)
Ask the rep once, in a single message: their full name, work email, and whether they already have
an Apollo sequence for this (name) or want one created.
Then, without further prompting:
- Slack ID: `slack_search_users` on their name -> capture the U******** id.
- Apollo sender mailbox: `apollo_email_accounts_index` -> their Gmail mailbox id (confirm if >1).
- Sequence: `apollo_emailer_campaigns_search` by the name they gave. If none, offer to create one
  with `apollo_sequences_create` using the standard cadence (day-1 manual email + call + LinkedIn
  connection, day-3 call, day-5 LinkedIn video, day-7 email, day-8 call) and the four
  Gather_* merge variables. Capture the sequence id + name.
Write all of this into `$BASE/hopper/rep_config.json`, and mirror sequence_id, sequence_name, and
sender_email_account_id into `$BASE/hopper/apollo_config.json`. Confirm the IDs you wrote.

## Step 3 — Build the hopper (automatic, needs their account list)
Ask the rep to paste their assigned accounts (names, or account,domain). For each, run the
`account-scoring` skill (Fit x Signal). Write `$BASE/hopper/hopper.jsonl`, one JSON object per line,
ranked best-first, schema:
{rank, account, domain, verdict, fit, signal, confidence, top_move, status:"todo",
last_worked_at:null, sequence_target:null, scored_at:"<today>"}.
Verdict: STRIKE = Fit>=70 and Signal>=70; NURTURE = Fit>=70, Signal<70; QUALIFY = Fit 40-69;
KILL = either <40. Then run `python3 "$BASE/hopper/gate.py" status` and show the ranked queue.

## Step 4 — Apollo field wiring (HUMAN STEP — guide, do not automate)
The Apollo MCP cannot create custom fields or run the CSV import. Tell the rep to do this once in
the Apollo UI, and wait for them to confirm before continuing:
1. Settings -> Custom Fields (object: Contacts). Create: Gather_Email_Subject, Gather_Email_Body,
   Gather_Script, Gather_Connection_Note (Text).
2. In their sequence, set the day-1 email Subject and Body to those variables using the { } picker
   (never hand-type the token), and reference Gather_Script / Gather_Connection_Note on the call
   and LinkedIn steps.
Point them to `$BASE/hopper/APOLLO_SETUP.md` for the exact clicks. Note: per run they import that
day's apollo-import.csv, matching on Email.

## Step 5 — Register the scheduled tasks (automatic)
Register two durable scheduled tasks via the scheduler:
- `apollo-morning-driver`: cron = rep_config.morning_cron; prompt = the full contents of
  `$BASE/hopper/MORNING_DRIVER.md` with BASE set to the absolute path and the Slack DM target set
  to rep_config.slack_user_id; notifyOnCompletion true.
- `apollo-weekly-digest`: Friday early afternoon; prompt = run `python3 "$BASE/hopper/digest.py"`
  and Slack the output to rep_config.slack_user_id; notifyOnCompletion true.
Confirm both registered with their next run times.

## Step 6 — Bank approvals (HUMAN STEP — instruct clearly)
Tell the rep: open Cowork's Scheduled panel, find apollo-morning-driver, click Run now once, and
approve each tool prompt (Clay, Apollo, Slack). Explain plainly: skip this and the automated 7am
runs fire but do nothing, because an unattended run cannot answer a permission prompt. Offer to
watch for the next run and confirm it produced a Slack report + run log.

## Close
Summarize in one screen: what is now automatic (account pick, research, sourcing, enrichment,
content, contact creation, staging, reporting, weekly digest) and the only human touches left
(the Apollo field wiring done once, the Run-now click once, then per-account enroll confirm +
the bespoke sends). Voice rules apply to anything you draft: no em dashes, no AI tells.

## Guardrails
- Never run the Apollo add-to-sequence or activate tools during onboarding. Onboarding only sets
  up; sending happens later, gated by the rep.
- Do not invent IDs. Every Slack/Apollo id must come from a live tool call in this session.
- If a tool is unavailable, say so plainly and tell the rep what to connect, rather than faking it.
