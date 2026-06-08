# Apollo Pipeline Orchestrator — Build Tracker

**Goal:** one command on an account name runs research → ICP contact find/enrich → personalized email + call/video scripts → upload to a premade Apollo sequence. Separately, when a contact responds, auto-fire lead scoring on responders (filtered) and Slack-notify on all responders.

**Approach:** rebuild on top of the existing `pipeline-generation` skill. Source archived. Add a separate response-watcher trigger.

Last updated: 2026-05-29 (all watcher decisions answered or defaulted)

---

## Architecture

**Orchestrator (push side):**
1. Peter types account name + triggers the orchestrator
2. Pull existing research from disk, or run fresh
3. Find ICP contacts at the account, enrich them (no scoring at this point)
4. Generate personalized email + call/video scripts per contact
5. Push all enriched contacts + first-touch content into a runtime-selected Apollo sequence

**Response watcher (pull side, separate skill + scheduled task):**
6. Every 15 min, poll Gmail for new replies from contacts in active Apollo sequences
7. Classify the reply:
   - **Real response:** auto-fire `lead-scoring-and-handoff` on the lead, drop handover doc in `OUTPUTS/Lead Workflow/`, Slack DM Peter with link + score summary
   - **OOO / wrong person:** do NOT auto-score. Slack DM Peter with the reply text and "needs guidance" tag
8. In both cases, log the reply against the contact so we don't re-process it

---

## Component status

| # | Component | Status | Notes |
|---|---|---|---|
| 1 | Orchestrator skill (single-command driver) | PACKAGED | `gather-apollo-pipeline.skill` ready at `OUTPUTS/Apollo Pipeline Orchestrator/`. Step 4b invokes `linkedin-video-dm`. Step 5b writes enrolled contacts to watcher state file. Needs Peter to install via Cowork skill installer. |
| 2a | Account research (existing record) | READY | `account-scoring` already implements "check disk, reuse if fresh". Reuse. |
| 2b | Account research (fresh) | READY | `account-research` skill installed. |
| 3a | ICP contact finder | READY | `apollo:prospect`. |
| 3b | Contact enrichment | READY | `apollo:enrich-lead`. |
| 4a | Email script generation | READY | `gather-cold-email` installed. |
| 4b | LinkedIn DM video script (doubles as call opener) | READY | `linkedin-video-dm` installed. Orchestrator wired to invoke it with fresh-connect framing per contact. One script, used for both LinkedIn DM and call opener. |
| 5 | Apollo sequence load | READY | `apollo:sequence-load`. |
| 6 | Response detection (Gmail watcher) | PACKAGED | `gather-apollo-response-watcher.skill` ready at `OUTPUTS/Apollo Pipeline Orchestrator/`. Self-registers a 15-min scheduled task on first run. Polls Gmail for replies from contacts in `state/active-contacts.jsonl`. |
| 7 | Reply classifier (OOO / wrong-person / real) | PACKAGED | Classifier patterns in `gather-apollo-response-watcher-skill/references/classifier-patterns.md`. Tuning log inside that file for future updates. |
| 8 | Auto-fire lead scoring on real responses | READY (once watcher exists) | `lead-scoring-and-handoff` installed. Watcher invokes it. |
| 9 | Handover doc delivery | READY | `lead-scoring-and-handoff` outputs branded .docx to `OUTPUTS/Lead Workflow/`. Watcher just needs to pass lead + company. |
| 10 | Slack notification | WIRED | Slack DM Peter via `slack_send_message`. Three formats by classification (real / OOO / wrong-person). Spec inside the watcher SKILL.md step 5. |

---

## Locked design decisions

1. **Contact volume per run:** push every ICP contact Apollo returns for the account. No cap.
2. **Apollo sequence selection:** picked at runtime. Iterate as the play library grows.
3. **No pre-load score gate.** Score runs only after a response.
4. **Personalization:** fully personalized first-touch per contact. No `{{custom_field}}` templating on touch 1.
5. **Response watcher = Gmail.** Apollo sends via Peter's Gmail OAuth, so replies land in his inbox. Apollo MCP reply-reading blocked on internal politics — Gmail is the path.
6. **Response filter:** filter OOO + wrong-person from auto-scoring. Still notify Peter on every reply so he can tune classification over time.
7. **Slack DM Peter on every response.** Classification decides format, not whether to notify.
8. **Handover docs:** `OUTPUTS/Lead Workflow/[FirstName-LastName]-[Company]-Handover.docx` (matches what lead-scoring-and-handoff already writes).
9. **Polling cadence:** every 15 min. Confirmed.
10. **Slack target:** DM Peter. Confirmed.

---

## Next actions (in order)

1. **Peter:** install `gather-apollo-pipeline.skill` via Cowork skill installer.
2. **Peter:** install `gather-apollo-response-watcher.skill` via Cowork skill installer.
3. **Peter:** uninstall the old `pipeline-generation` skill via Cowork UI (its slot is now taken by the orchestrator).
4. **Both:** dry-run end-to-end on one test account. Push a contact, send a reply manually, verify the watcher classifies, fires scoring, drops the handover doc, sends Slack DM.
5. **Both:** start tuning the classifier patterns file as Peter labels misclassifications during real use.

---

## Archive notes

- 2026-05-29: archived `OUTPUTS/Programs/Pipeline-Gen/` to `OUTPUTS/_Archive/Pipeline-Gen-archived-2026-05-29/`. Reference material for the rewrite.
