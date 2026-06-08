---
name: gather-apollo-pipeline
description: Single-command Apollo pipeline orchestrator for Gather AI. Takes a named account, runs research (pulled or fresh), finds and enriches every ICP contact at that account, generates a personalized email and a LinkedIn DM video script (also used as a call opener) per contact, then loads all of them into a runtime-selected Apollo sequence. Lead scoring is NOT run here, it fires separately when contacts respond, via the gather-apollo-response-watcher skill. Use this skill any time Peter says "Run Apollo pipeline on [account]", "Push [account] to Apollo", "Load [account] into a sequence", "Apollo orchestrator on [account]", "Generate Apollo sequence for [account]", or any phrasing that means "do the whole push-side prospecting flow on this logo". Do NOT use for one-off research (use account-research), pamphlet generation (use account-attack-plan), MQL-to-SAL handover scoring (use lead-scoring-and-handoff), or 1:1 manager updates (use monday-1on1-update).
---

# Gather Apollo Pipeline Orchestrator

End-to-end push-side prospecting for one account: research → contact discovery → enrichment → personalized first-touch generation → Apollo sequence load. Lead scoring happens on the pull side via `gather-apollo-response-watcher` when contacts reply, not here.

## When this skill runs

Peter has identified an account he wants to push into outbound and wants the whole flow run in one shot. The output is: every ICP contact at that account loaded into an Apollo sequence with a personalized first touch (email + call/video script) attached to each.

## Inputs

Required:
- Account name (company)

Strongly preferred (asked if missing):
- ICP override (if Peter wants something other than the seed ICP of "VP Operations at Logistics company with 3+ facilities")
- Sub-org focus (if the account is huge, e.g. "Honda Manufacturing of Alabama only, not all of Honda North America")

The Apollo sequence ID is asked at runtime (step 5), not upfront.

## Execution sequence

Run these in order. If a step has no useful output, log it and continue. Do not block the full pipeline on a single soft failure.

### Step 1 — Account research (pull or fresh)

Check `$BASE/../[Account]/` for a research file less than 14 days old. If one exists, read it. If not, invoke the `account-research` skill on the account and wait for its output. Either way, the orchestrator needs the research file in hand before contact discovery.

Read the research file. Extract:
- Sub-org map (if the account has distinct divisions/business units)
- Trigger events from the last 90 days
- Strategic context (any specific operational pain or initiative Gather can speak to)

These three pieces feed the personalization in step 4.

### Step 2 — Confirm ICP and sub-org scope with Peter

Show Peter:
- The ICP that will be applied (default seed: VP Operations at Logistics company with 3+ facilities — override if Peter set one)
- The sub-orgs identified in research

Ask Peter once: "Run against the whole account, or scope to a sub-org?" If unclear, default to whole account.

### Step 3 — Find + enrich ICP contacts

Invoke `apollo:prospect` with:
- Company: the account (or sub-org if scoped)
- Title pattern: matches the ICP (default: VP / Director of Operations, Supply Chain, Logistics, Distribution)
- Geography: US-based unless Peter specifies otherwise

Then run `apollo:enrich-lead` on each contact returned. Collect: full name, title, work email, mobile if available, LinkedIn URL, tenure if available.

Push every contact returned. No volume cap. No score gate at this stage.

If `apollo:prospect` returns zero contacts, stop and tell Peter: the ICP filter returned nothing for this account. Suggest broadening title or removing geography.

### Step 4 — Generate first-touch content per contact

For each enriched contact, generate two pieces of content:

**Step 4a — Email (`gather-cold-email` skill):**
Invoke `gather-cold-email` with the contact's full context (name, title, company, sub-org if applicable) plus the research file extracts from step 1 (trigger event, strategic context, sub-org pain). Output: one personalized email per contact, in Peter's voice. No templates. No `{{custom_field}}` slots. Every email must reference something true and specific about this buyer this week.



**Step 4b — LinkedIn DM video script (`linkedin-video-dm` skill):**

Invoke `linkedin-video-dm` for every enriched contact. Pass:
- Contact: first name, last name, title, company (and sub-org if scoped)
- Research context: trigger event, strategic context, and the sub-org pain extract from step 1
- Connection state framing: treat as "fresh connect" — assume a freshly accepted LinkedIn connection. Apollo prospecting doesn't map cleanly to the skill's fresh-connect or warm-signal options. Fresh connect is the safer default because it cues the hook toward an observation about the lead/company rather than an engagement signal we don't actually have.

Output: a 30-45 second script. **The same script doubles as the call opener** — the MDR uses it for both the LinkedIn DM video recording and as a phone/voicemail opener. One asset, two channels.

Every contact in this orchestrator is treated as a curated lead — the depth of research + ICP targeting earns every contact the personal-touch treatment. Do not skip any contact for being "low priority."

### Step 5 — Apollo sequence selection + load

Ask Peter at runtime: "Which Apollo sequence are we loading into?" Show him the sequence options he has access to (via Apollo MCP if listing is supported, else just ask him to paste a sequence ID or name).

Once selected, invoke `apollo:sequence-load` with:
- The contact list (from step 3, enriched)
- The personalized first-touch content per contact (from step 4)
- The selected sequence ID

`apollo:sequence-load` handles dedup, contact creation, and enrollment.

### Step 5b — Log enrolled contacts to watcher state

For every contact actually enrolled in the sequence (not duped out, not failed), append one line to `$BASE/state/active-contacts.jsonl`:

```
{"email": "...", "first_name": "...", "last_name": "...", "company": "...", "sequence_id": "...", "enrolled_at": "ISO-8601"}
```

This is the file the `gather-apollo-response-watcher` skill reads every 15 min to know whose Gmail to watch. If the file or state folder does not exist, create them. Append-only — do not overwrite. Skipping this step breaks the response-watcher flow silently.

### Step 6 — Report back

Output a one-screen summary to Peter:
- Account researched (and whether fresh or pulled)
- N contacts found, N enriched, N pushed to sequence, N logged to watcher state
- Sequence name + ID they landed in
- Any contacts skipped (with reason: missing email, dup, enrichment failed)
- Step 4b status (ran for N contacts via `linkedin-video-dm`)
- Where the orchestrator output log was saved: `$BASE/runs/[YYYY-MM-DD]-[Account]-run.md`

Then save that one-screen summary as the run log at the path above.

## Voice and tone constraints

Every line of generated copy across step 4 must follow Peter's writing rules:
- No em dashes
- No AI tells ("leverage", "unlock", "robust", "in today's fast-paced", "I hope this finds you well", "circle back")
- Active voice. Contractions normal.
- Numbers and mechanisms over adjectives.
- Account-specific. Generic = unusable.

The full list lives in `ABOUT ME/anti-ai-writing-style.md`. Both `gather-cold-email` and `linkedin-video-dm` enforce this internally. If either output looks generic or AI-flavored, flag it back to Peter rather than passing it through.

## When this skill should NOT run

- Just doing research on an account → use `account-research`.
- Building a pamphlet packet → use `account-attack-plan`.
- A specific lead has responded and needs scoring + AE handover → use `lead-scoring-and-handoff`.
- Manager update / forecast slide → use `monday-1on1-update`.
- Cost/ROI deck for a deal → use `gather-cost-roi-deck`.

## Companion skill

`gather-apollo-response-watcher` (separate skill, also being built) handles the pull side: it polls Gmail every 15 min for replies from contacts in active sequences, classifies them (real / OOO / wrong-person), and on real responses auto-fires `lead-scoring-and-handoff` to produce a handover doc. Slack DM to Peter on every reply regardless of classification.
