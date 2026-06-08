# Apollo per-contact content: one-time setup + per-run upload

Apollo sequence emails use ONE shared template with `{{merge}}` variables. To send each
contact their bespoke copy (and show reps the right script per contact), we store the
generated content in Apollo CUSTOM FIELDS and reference those fields as merge tags. The
Apollo MCP can't create custom fields, wire templates, or run imports, so those are one-time
UI actions. After setup, each run is a 1-minute CSV import.

## Step 1 — Create 4 custom fields (one time, ~3 min)
1. Top-right gear icon -> **Settings**.
2. Left nav -> **Custom Fields** (under the Data / General section).
3. Make sure the object selector at the top is **Contacts/People** (not Accounts).
4. Click **+ Add Custom Field** and create each of these. Type = **Text** for all (Text holds long values; if a "Paragraph/Long text" type is offered, use it for the two body fields):

   | Field name (type exactly) | Holds |
   |---|---|
   | `Gather_Email_Subject` | day-1 email subject |
   | `Gather_Email_Body` | day-1 bespoke email body |
   | `Gather_Script` | 30-45s script (call opener + LinkedIn video) |
   | `Gather_Connection_Note` | LinkedIn connection note (<300 chars) |

5. Save each. They now appear on every contact record and in the email variable picker.

## Step 2 — Wire the sequence ONCE (~5 min)
Open sequence **"Claude Research -> Execution Queue"** -> it stays INACTIVE for now.

**Day-1 email step (position 1):** click the step to edit the email.
- Subject field: click the **variable / { } button** -> search "Gather_Email_Subject" -> insert. The subject box should now read only the inserted `{{...}}` token.
- Body: delete any existing template text. Click the **{ } variable button** -> insert **Gather_Email_Body**. The body should be ONLY that token.
- CRITICAL: always insert via the variable picker, never hand-type the token. Apollo assigns the real merge key when the field is created, and the picker guarantees it matches.
- Save the step.

**Call steps (Day 1, Day 3, Day 8) and the Day-5/6 LinkedIn video step:** open each step's note/instructions, click the variable button, insert **Gather_Script**. (If the note field does not offer variables, leave a line like "Script: see Gather_Script on the contact record" — the field is visible on the contact panel during the task.)

**Day-1 LinkedIn connection step:** insert **Gather_Connection_Note** into the message/note.

Once the day-1 email Body = the Gather_Email_Body variable, the auto_email sends each contact's
bespoke copy. You review before activating, so auto-send is safe (your review is the gate).
GUARD: never activate a contact before the import (Step 3) has populated their fields, or an
empty field sends a blank email.

## Step 2b — Verify once (2 min, do this before trusting it)
DHL's 6 contacts are already enrolled (paused) with their apollo-import.csv ready. After Steps 1-3:
open one DHL contact in the sequence -> Preview the day-1 email -> confirm it renders the bespoke
body (not an empty token). If it renders, setup is correct and permanent.

## Step 3 — Per run: import the CSV (1 minute)
Each run the pipeline writes `apollo-import.csv` (headers already match the field names above).
In Apollo: Import -> CSV -> match on **Email** -> map each `Gather_*` column to its custom field
-> run. This updates the already-created contacts with their per-contact content. Then review
and activate the sequence.

## What's automated vs manual
- Automated (pipeline): research, sourcing, enrichment, content generation, contact creation in
  Apollo, paused enrollment, and writing the import-ready CSV.
- Manual (Apollo UI, unavoidable with current tools): the one-time field creation + template
  wiring (Steps 1-2), and the per-run CSV import (Step 3). All quick.

## Field <-> CSV column map (for the importer)
email -> match key
Gather_Email_Subject -> Gather_Email_Subject
Gather_Email_Body -> Gather_Email_Body
Gather_Script -> Gather_Script
Gather_Connection_Note -> Gather_Connection_Note
