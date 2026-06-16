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
Do every step you can automatically. Stop and ask only where a human must act. Confirm each
milestone with a clean visual line.

> ⏳ **This setup takes 15–30 minutes** while Claude scores your accounts and wires the config.
> Most of the time is hands-off. You do not need to babysit the session.

## Prerequisites (must already be satisfied)

Before starting, confirm ALL of the following are true. If any are missing, stop and tell the
rep exactly what to do:

- ✅ Apollo account with a Gmail mailbox **connected and active** (required for sender identity
  and sequence enrollment).
- ✅ `rep_config.json` exists and contains `name`, `email`, and `sequence_id`. This file is either
  pre-filled by the rep or discovered from a prior session. **This skill does not interview for
  identity — it reads what is already there.**
- ✅ The repo "Apollo Pipeline Orchestrator" is accessible in this Cowork session (either added
  via the **Context** panel or cloned into the user's OUTPUTS).

---

## Step 0 — Locate the toolkit

Find the orchestrator folder: search the user's OUTPUTS for `Apollo Pipeline Orchestrator/hopper/gate.py`.
Set `BASE` = that folder.

**If not found:**
```
❌ STEP 0 — Toolkit not found

The repo must be in your Cowork context to run setup.
Fix: Add "Apollo Pipeline Orchestrator" to your Context panel (or clone it into OUTPUTS),
then re-trigger this skill.
```

**If found:**
```
✅ STEP 0 — Toolkit located at <BASE>
```

All paths below are under `BASE`.

---

## Step 1 — Scaffold (automatic)

Run: `python3 "$BASE/hopper/setup.py"`

**Expected output:**
```
✅ STEP 1 — Workspace scaffolded
   Created: state/
   Created: runs/
   Created: rep_config.json
   Created: apollo_config.json
```

---

## Step 2 — Identity (automatic — read only)

Open `$BASE/hopper/rep_config.json`. Do not ask the rep for name, email, or sequence — these
must already be present.

**If any required field is missing (`name`, `email`, or `sequence_id`):**
```
❌ STEP 2 — Missing required identity fields

Your rep_config.json is missing required fields. Please fill:
  • name
  • email
  • sequence_id

Then re-trigger this skill.
```

**If all fields are present, resolve the live IDs and write back:**
- Slack ID: `slack_search_users` on `name` → capture `U********`
- Apollo sender mailbox: `apollo_email_accounts_index` → capture Gmail mailbox id
- Sequence: `apollo_emailer_campaigns_search` by `sequence_id` or name → confirm id + name

Mirror `sequence_id`, `sequence_name`, and `sender_email_account_id` into
`$BASE/hopper/apollo_config.json`.

**Expected output:**
```
✅ STEP 2 — Identity resolved
   Slack user_id:     U********
   Apollo mailbox id:  <mailbox_id>
   Sequence id:       <sequence_id>
   Sequence name:     <sequence_name>
```

---

## Step 3 — Build the hopper (automatic)

The rep must have already provided their account list (via context, paste, or prior message).
For each account, run the `account-scoring` skill (Fit × Signal).

Write `$BASE/hopper/hopper.jsonl`, one JSON object per line, ranked best-first, schema:
```json
{rank, account, domain, verdict, fit, signal, confidence, top_move, status:"todo",
 last_worked_at:null, sequence_target:null, scored_at:"<today>"}
```

**Verdict rules:**
- STRIKE = Fit ≥70 and Signal ≥70
- NURTURE = Fit ≥70, Signal <70
- QUALIFY = Fit 40–69
- KILL = either <40

Then run `python3 "$BASE/hopper/gate.py" status`.

**Expected output:**
```
✅ STEP 3 — Hopper built
   Accounts scored:    <N>
   STRIKE:             <N>
   NURTURE:            <N>
   QUALIFY:            <N>
   KILL:               <N>
   Ranked queue ready. Top account: <top_account>
```

---

## Step 4 — Apollo field wiring (HUMAN STEP — guide only)

The four Gather custom fields already exist in the workspace. The rep only needs to wire them
into their own sequence template. The Apollo MCP cannot do this, so the rep must do it **once**
in the Apollo web UI. Wait for them to confirm before continuing.

**Exact instructions:**
1. Open your target sequence → edit the **day-1 email step**
   - Click into the **Subject** field → use the **{ }** picker → select `Gather_Email_Subject`
   - Click into the **Body** field → use the **{ }** picker → select `Gather_Email_Body`
   - **Never hand-type the token** — always use the picker.
2. In the same sequence, edit the **call step** → reference `Gather_Script` via the picker.
3. Edit the **LinkedIn connection step** → reference `Gather_Connection_Note` via the picker.

Point them to `$BASE/hopper/APOLLO_SETUP.md` for screenshots. Note: per run they import that
day's `apollo-import.csv`, matching on Email.

**Expected output (after rep confirms):**
```
✅ STEP 4 — Apollo fields wired (human confirmed)
   Custom fields created and sequence template set.
```

---

## Step 5 — Register scheduled tasks (automatic)

Register two durable scheduled tasks via the scheduler:

- `apollo-morning-driver`
  - cron = `rep_config.morning_cron`
  - prompt = full contents of `$BASE/hopper/MORNING_DRIVER.md` with `BASE` set to the absolute path
    and Slack DM target set to `rep_config.slack_user_id`
  - `notifyOnCompletion` = true

- `apollo-weekly-digest`
  - Friday early afternoon
  - prompt = run `python3 "$BASE/hopper/digest.py"` and Slack the output to `rep_config.slack_user_id`
  - `notifyOnCompletion` = true

**Expected output:**
```
✅ STEP 5 — Scheduled tasks registered
   apollo-morning-driver   → next run: <time>
   apollo-weekly-digest    → next run: <time>
```

---

## Step 6 — Bank approvals (HUMAN STEP — instruct clearly)

Tell the rep:

> Open Cowork's **Scheduled** panel, find `apollo-morning-driver`, click **Run now** once, and
> approve each tool prompt (Clay, Apollo, Slack) as it appears.

Explain plainly: skip this and the automated 7am runs fire but do nothing, because an unattended
run cannot answer a permission prompt.

**Expected output (after rep confirms):**
```
✅ STEP 6 — Tool approvals banked (human confirmed)
   Clay, Apollo, and Slack prompts approved once.
   Future 7am runs will fire unattended.
```

---

## Close — Setup Summary

```
🎯 Setup complete. Here is what is now automatic:

✅ Account pick      — top-scored account pulled from hopper each morning
✅ Research          — Clay finds VP/Director+ contacts + enriches emails
✅ Content           — bespoke email, call script, LinkedIn note per contact
✅ Staging           — contacts written to apollo-import.csv
✅ Reporting         — Slack DM with staged batch summary
✅ Weekly digest     — Friday rollup of runs, enrollments, replies, hopper depth

🖐️ Human touches remaining:
   • Apollo field wiring    → done once (Step 4)
   • Run-now approval       → done once (Step 6)
   • Per-account enroll     → you review and confirm before send
   • Bespoke sends          → calls, LinkedIn videos, manual emails
```

---

## Guardrails

- Never run the Apollo add-to-sequence or activate tools during onboarding. Onboarding only sets
  up; sending happens later, gated by the rep.
- Do not invent IDs. Every Slack/Apollo id must come from a live tool call in this session.
- If a tool is unavailable, say so plainly and tell the rep what to connect, rather than faking it.
