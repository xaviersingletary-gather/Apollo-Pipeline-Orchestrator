# Apollo UI Wiring — Wire Gather Custom Fields Into YOUR Sequence

The 4 Gather custom fields (`Gather_Email_Subject`, `Gather_Email_Body`, `Gather_Script`, `Gather_Connection_Note`) already exist in the Apollo workspace. They were created once for all reps. **You do NOT create fields. You pick them from a menu and drop them into YOUR sequence template.**

This guide shows every click so a new user can follow it cold. If you have never wired custom fields in Apollo, read every line. If you have done it before, skip to the checklist at the bottom.

Time: 5 minutes.
Prerequisite: You must already have an Apollo sequence (or know its name). If not, create one first or ask Claude to make it for you.

---

## Step 1 — Open YOUR sequence

1. Go to **Engage** → **Sequences** in the left Apollo nav.
2. Find the sequence you want to use (e.g. "Gather Outbound Q2").
3. Click the sequence name to open it.
4. Click **Steps** (top tab).

What you see:
```
┌─────────────────────────────────────────────────────────┐
│  Sequences  >  Gather Outbound Q2                       │
│  [Overview] [Steps] [Settings] [Analytics]              │
│                                                         │
│  Step 1: Email    Day 1  [Edit]                         │
│  Step 2: Call     Day 1  [Edit]                         │
│  Step 3: LinkedIn Day 1  [Edit]                         │
│  Step 4: Call     Day 3  [Edit]                         │
│  Step 5: LinkedIn Day 5  [Edit]                         │
│  Step 6: Email    Day 7  [Edit]                         │
│  Step 7: Call     Day 8  [Edit]                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 2 — Wire the Day-1 Email Subject

1. Click **Edit** on **Step 1: Email (Day 1)**.
2. Click into the **Subject** field.
3. Click the **{ }** button (the curly-brace icon to the right of the Subject field).

What you see:
```
┌─────────────────────────────────────────────────────────┐
│  Edit Email Step                                        │
│                                                         │
│  Subject    [___________________________] { }           │
│                              ^^^^^^^                    │
│                              click this button          │
└─────────────────────────────────────────────────────────┘
```

4. A dropdown appears with custom field categories.
5. Scroll or search for **Gather_Email_Subject**.
6. Click it. The Subject field now shows only the merge token — no hand-typed text.

Correct result:
```
Subject: {{custom_field_123_Gather_Email_Subject}}
```

**NEVER type the token by hand.** Always use the `{ }` picker. Hand-typed tokens will NOT merge at send time and the email will ship with literal `{{...}}` text.

---

## Step 3 — Wire the Day-1 Email Body

1. In the same Step 1 edit panel, click into the **Body** field.
2. Delete any existing template text in the Body.
3. Click the **{ }** button next to the Body field.
4. Search for **Gather_Email_Body**.
5. Click it.

Correct result — Body field should contain ONLY this token:
```
Body: {{custom_field_456_Gather_Email_Body}}
```

**Again: do NOT type this yourself.** If you see any other text in the Body field (greetings, signatures, boilerplate), delete it. The merge token must be the ONLY content. The actual email body is populated per-contact via CSV import before sending.

6. Click **Save Step**.

---

## Step 4 — Wire the Call Step Notes

The call step uses `Gather_Script` as the opener script that the rep reads when making the call.

1. Back in the sequence Steps tab, click **Edit** on **Step 2: Call (Day 1)**.
2. Look for the **Notes / Call Script** field (sometimes labeled "Call Instructions" or "Notes").
3. Click the **{ }** button next to that field.
4. Search for **Gather_Script**.
5. Click it.

Correct result:
```
Notes: {{custom_field_789_Gather_Script}}
```

6. Click **Save Step**.

7. Repeat for **Step 4: Call (Day 3)** and **Step 7: Call (Day 8)** — same process, same field `Gather_Script`.

---

## Step 5 — Wire the LinkedIn Connection Step

1. Back in the sequence Steps tab, click **Edit** on **Step 3: LinkedIn Connection Request (Day 1)**.
2. Look for the **Message** or **Connection Note** field.
3. Click the **{ }** button next to that field.
4. Search for **Gather_Connection_Note**.
5. Click it.

Correct result:
```
Message: {{custom_field_012_Gather_Connection_Note}}
```

6. Click **Save Step**.

---

## Step 6 — Verify Before Trusting

Before your first run, preview a contact to confirm the merge works.

1. In Apollo, go to **People** → find any contact already in your sequence.
2. Open their record.
3. Scroll to the **Custom Fields** section on the contact panel.
4. Verify that `Gather_Email_Subject`, `Gather_Email_Body`, `Gather_Script`, and `Gather_Connection_Note` all appear as fields. If they do not, something is wrong — ask for help.

**Guard: if the custom fields do NOT appear on the contact record, STOP.** The fields were not wired correctly or the contact is not in the right sequence.

---

## Quick Checklist (for experienced users)

If you have done this before, just run through these 5 checks:

- [ ] Day-1 email Subject = `Gather_Email_Subject` via `{ }` picker
- [ ] Day-1 email Body = `Gather_Email_Body` via `{ }` picker (ONLY token, no other text)
- [ ] Day-1 call Notes = `Gather_Script` via `{ }` picker
- [ ] Day-3 call Notes = `Gather_Script` via `{ }` picker
- [ ] Day-8 call Notes = `Gather_Script` via `{ }` picker
- [ ] Day-1 LinkedIn Message = `Gather_Connection_Note` via `{ }` picker
- [ ] Sequence is INACTIVE until you import a CSV and review

---

## What Is Automated vs Manual

| Action | Who Does It | When |
|--------|------------|------|
| Research contacts | Claude / Clay | Every morning |
| Write personalized email per contact | Claude | Every morning |
| Write call script per contact | Claude | Every morning |
| Write LinkedIn note per contact | Claude | Every morning |
| Create contacts in Apollo | Claude | Every morning |
| Export `apollo-import.csv` | Claude | Every morning |
| **Wire custom fields into sequence template** | **You** | **Once, right now** |
| Import `apollo-import.csv` into Apollo | You | Per run (1 minute) |
| Review and activate | You | Per run |

---

## Common Mistakes

| Mistake | Why It Breaks | Fix |
|---------|--------------|-----|
| Hand-type `{{Gather_Email_Subject}}` instead of using the `{ }` picker | Apollo assigns internal IDs. Hand-typed tokens are treated as literal text and ship as-is. | Delete, re-insert via picker. |
| Leave boilerplate text in the Body field alongside the merge token | The body will contain both the boilerplate AND the merged content, producing a garbled email. | Delete ALL text in Body, leave ONLY the merge token. |
| Activate a contact before importing the CSV | Custom fields are empty until the CSV import fills them. Activating before import sends a blank email. | Always import CSV first, then activate. |
| Sequence is ACTIVE instead of INACTIVE during setup | If contacts are already enrolled, an accidental activation sends before you review. | Keep the sequence INACTIVE until your first run. |

---

## What Per Run Looks Like After This One-Time Setup

Each morning the pipeline writes an `apollo-import.csv` with one row per contact. You do this in 60 seconds:

1. Apollo → **Import** → **CSV** → upload `apollo-import.csv`
2. Match on **Email**
3. Map `Gather_Email_Subject` → `Gather_Email_Subject`
4. Map `Gather_Email_Body` → `Gather_Email_Body`
5. Map `Gather_Script` → `Gather_Script`
6. Map `Gather_Connection_Note` → `Gather_Connection_Note`
7. Run import
8. Review contacts → Activate

Done.
