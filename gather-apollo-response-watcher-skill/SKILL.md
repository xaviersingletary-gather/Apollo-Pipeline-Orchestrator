---
name: gather-apollo-response-watcher
description: Background poller that watches Gmail every 15 minutes for replies from contacts enrolled in Apollo sequences by the gather-apollo-pipeline orchestrator. Classifies each reply as real / out-of-office / wrong-person. On real responses, auto-fires the lead-scoring-and-handoff skill, drops a branded handover .docx in $BASE/../Lead Workflow/, and Slack-DMs the rep with the lead score summary + doc link. On OOO or wrong-person replies, Slack-DMs the rep the reply text with a 'needs guidance' tag and does NOT auto-score. Use this skill when the rep says 'run the response watcher', 'check for Apollo responses', 'watch Gmail for replies', 'check who responded to my sequences', or any phrasing about polling for sequence replies. Also runs automatically via a scheduled task on a 15-minute interval. Do NOT use for sending outbound (use gather-apollo-pipeline), scoring leads outside the response context (use lead-scoring-and-handoff directly), or general inbox triage (use a Gmail tool directly).
---

# Gather Apollo Response Watcher

Pull-side companion to `gather-apollo-pipeline`. Polls Gmail every 15 min for replies from sequence-enrolled contacts, classifies each one, and routes accordingly: real responses auto-fire scoring, soft replies route to Peter for tuning.

## When this skill runs

Two trigger modes:
- **Automatic:** a scheduled task fires this skill every 15 min.
- **Manual:** the rep says "run the response watcher" or equivalent. Same execution path.

On first invocation, this skill registers the scheduled task if one does not already exist. Subsequent invocations skip registration.

## State files

Two files in `$BASE/state/`:

- `active-contacts.jsonl` — appended by `gather-apollo-pipeline` every time a contact is enrolled in a sequence. One line per enrollment:
  ```
  {"email": "...", "first_name": "...", "last_name": "...", "company": "...", "sequence_id": "...", "enrolled_at": "ISO-8601"}
  ```
- `processed-replies.jsonl` — appended by this watcher each time a reply has been handled. Used to skip already-processed messages on the next run:
  ```
  {"thread_id": "...", "message_id": "...", "contact_email": "...", "classification": "real|ooo|wrong_person", "processed_at": "ISO-8601"}
  ```

If either file does not exist, create it empty and continue. A missing state file is not a failure mode.

## Execution sequence

### Step 1 — Self-register the scheduled task (first run only)

Check `$BASE/state/scheduler-registered.flag`. If it does not exist:
- Invoke `mcp__scheduled-tasks__create_scheduled_task` with a 15-minute recurring interval and the trigger `gather-apollo-response-watcher`.
- Write the flag file with the task ID inside.
- Continue.

If the flag exists, skip. Do not re-register.

### Step 2 — Load active contacts

Read `state/active-contacts.jsonl`. Build a unique set of contact emails. If the set is empty, log "no active contacts" and exit cleanly. No Slack ping for empty runs.

### Step 3 — Poll Gmail for new replies

For each unique contact email, invoke `mcp__61434f25-3dd6-4005-ba30-f39d9add50ab__search_threads` with a query that matches threads `from:` that contact in the last 24 hours (overlap window to catch slow Gmail indexing).

For each thread returned, get the latest message via `get_thread`. Compare its `message_id` against `processed-replies.jsonl`. If already processed, skip. Otherwise it's a new reply — proceed.

### Step 4 — Classify the reply

Read the reply body and apply this classifier (lightweight, in-LLM, no external model needed):

**OOO (out of office):** any of the following patterns
- "out of office" / "OOO" / "out of the office"
- "on vacation" / "on holiday" / "on PTO" / "on leave" / "on parental leave"
- "will be back on [date]" / "returning [date]" / "limited access to email"
- Auto-reply formatting (single short message, third-person tone, no question to the sender)

**Wrong person:** any of the following patterns
- "no longer with the company" / "no longer here" / "has left"
- "you have the wrong person" / "I don't handle that" / "not my area"
- "please contact [X] instead" / "redirecting you to..."
- "remove me from your list" / "unsubscribe" / "do not email me"
- "this is not [name]" / "you've reached me in error"

**Real response:** everything else. Includes positive, negative, neutral, "tell me more," "not interested," "send more info," "let me think about it," etc. Anything substantive that the MDR/AE should see and decide on counts as real.

If the message is genuinely ambiguous, default to **real** and let Peter sort it. Bias toward false positives on "real" — under-classifying is safer than over-filtering.

### Step 5 — Take action based on classification

**For each real response:**
1. Invoke `lead-scoring-and-handoff` with `lead_name` (first + last) and `company` from the contact record.
2. Wait for it to produce the handover doc at `$BASE/../Lead Workflow/[First-Last]-[Company]-Handover.docx`.
3. Slack DM the rep via `mcp__33da6e8a-ebd8-480b-b763-9cc7d3f6caa4__slack_send_message`. Format:
   ```
   🔔 Response from [First Last] at [Company]
   Quadrant: [STRIKE/NURTURE/QUALIFY/IGNORE]   Lead band: [80+/50-79/<50]
   Reply: "[first 200 chars of reply]"
   Handover doc: [link or path]
   ```

**For each OOO response:**
1. Do NOT invoke scoring.
2. Slack DM the rep:
   ```
   📭 OOO from [First Last] at [Company]
   Reply: "[first 200 chars]"
   Needs guidance: is this an OOO worth scheduling follow-up for, or skip?
   ```

**For each wrong-person response:**
1. Do NOT invoke scoring.
2. Slack DM the rep:
   ```
   ❌ Wrong-person from [First Last] at [Company]
   Reply: "[first 200 chars]"
   Needs guidance: redirect to a named replacement, or remove from sequence?
   ```

### Step 6 — Log the processed reply

Append a new line to `processed-replies.jsonl` for every reply handled (regardless of classification). This prevents re-processing on the next run.

### Step 7 — Exit cleanly

No final Slack summary for the run itself. The per-response DMs are the output. Log to `$BASE/runs/watcher-[YYYY-MM-DD-HHMM].log` with: contacts checked, replies found, classifications, actions taken.

## Tuning over time

The classifier is intentionally simple in v1. As Peter receives the OOO and wrong-person DMs and confirms or overrides each one, update the pattern lists in `references/classifier-patterns.md`. v1 is a starting point, not a final state.

If Peter ever says "the classifier got [X] wrong" or "this should not have been classified as OOO," update the patterns file accordingly. Bias the patterns toward Peter's actual misses, not theoretical edge cases.

## Voice and tone for Slack DMs

Slack messages follow the same rules as the rest of Peter's outputs:
- No em dashes. No AI tells.
- Short. Glanceable on phone.
- Lead with the signal, not the framing.
- Don't apologize, don't pad, don't recap what Peter already knows.

## When this skill should NOT run

- Outbound push side (use `gather-apollo-pipeline`).
- Direct lead scoring without a response context (use `lead-scoring-and-handoff`).
- General inbox triage (use Gmail tools directly).
- Reading or summarizing entire threads (use Gmail tools or `enterprise-search:search`).
