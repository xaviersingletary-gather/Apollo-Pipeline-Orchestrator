# Team Setup — Stand up the Self-Driving Apollo Pipeline for yourself

You have Claude, Apollo, Clay, Gmail, and Slack connected. This gets you running in about
30 minutes. The toolkit is portable — it works wherever you copy this folder.

## Fastest path: just type "run apollo setup"
Install the `apollo-onboard` skill (in `apollo-onboard-skill/`, install via the Cowork skill
installer), then type **"run apollo setup"**. Claude does every automatable step for you and
pauses only for the three human-only bits: pasting your account list, creating the Apollo custom
fields in the UI, and clicking "Run now" once. The manual steps below are the same flow if you
prefer to drive it yourself or the skill isn't installed.

## What you're standing up
Every weekday morning, Claude pulls your top-scored account off a ranked hopper, finds and
enriches 20 Director+/VP contacts, writes a personalized email + call/LinkedIn script per
contact, stages them in your Apollo sequence (paused), and Slacks you a report. You approve
and send. See `hopper/MORNING_DRIVER.md` for the full daily flow.

---

## Step 0 — Copy the toolkit
Copy this entire `Apollo Pipeline Orchestrator` folder into your own Cowork workspace
(OUTPUTS/). Everything you need is inside it. Nothing points at another rep's machine.

## Step 1 — Scaffold (1 command)
In the folder, run:
```
python3 hopper/setup.py
```
This creates your `state/`, `runs/`, empty hopper, and a `rep_config.json` to fill in.

## Step 2 — Fill in your identity (hand this to Claude)
Open `hopper/rep_config.json`. Paste this to Claude:
> "Fill my rep_config.json. Find my Slack user ID with slack_search_users on my name. Find my
> Apollo sender mailbox id with apollo_email_accounts_index. Find or create my Apollo sequence
> and put its id + name in. My name is ___, email ___."

Then update `hopper/apollo_config.json` with your `sequence_id`, `sequence_name`, and
`sender_email_account_id` (same values), so the pipeline targets YOUR sequence.

## Step 3 — Build your hopper (hand this to Claude)
Give Claude your account list (paste names, or a CSV of account,domain). Then:
> "Score each of these accounts with the account-scoring skill (Fit x Signal), then write
> hopper/hopper.jsonl, one JSON object per line, ranked best-first, using this schema:
> {rank, account, domain, verdict, fit, signal, confidence, top_move, status:'todo',
> last_worked_at:null, sequence_target:null, scored_at:'<today>'}. Verdict rule: STRIKE = Fit>=70
> and Signal>=70; NURTURE = Fit>=70, Signal<70; QUALIFY = Fit 40-69; KILL = either <40."

Sanity-check: `python3 hopper/gate.py status` should list your ranked accounts.

## Step 4 — One-time Apollo wiring (you, in the Apollo UI)
Follow `hopper/APOLLO_SETUP.md`:
- Create 4 custom fields: `Gather_Email_Subject`, `Gather_Email_Body`, `Gather_Script`, `Gather_Connection_Note`.
- In your sequence, set the day-1 email Subject and Body to those merge variables via the `{ }`
  picker (do NOT hand-type the tokens), and reference `Gather_Script` / `Gather_Connection_Note`
  on the call and LinkedIn steps.
- Per run you import that day's `apollo-import.csv` (match on Email) to fill the fields.

## Step 5 — Register your scheduled tasks (hand this to Claude)
> "Register two durable scheduled tasks for me using the scheduler. Task 1 `apollo-morning-driver`:
> cron from rep_config morning_cron, prompt = the contents of hopper/MORNING_DRIVER.md with BASE
> set to this folder's absolute path and the Slack target set to my slack_user_id from rep_config.
> Task 2 `apollo-weekly-digest`: Friday early afternoon, runs `python3 hopper/digest.py` and Slacks
> me the output. notifyOnCompletion true on both."

## Step 6 — Bank tool approvals (you, once — critical)
In Cowork's **Scheduled** panel, find `apollo-morning-driver` and click **Run now** once.
Approve each tool prompt (Clay, Apollo, Slack) as it appears. Those approvals are stored on the
task, so every future 7am run fires unattended without stalling. **Skip this and your automated
runs will silently do nothing** (they can't answer a permission prompt at 7am).

---

## Daily life after setup
- Morning: Claude Slacks you "20 contacts staged across N accounts." You review, reply/confirm
  enroll per account, import that account's `apollo-import.csv`, then activate the sequence.
- STRIKE accounts wait for your review; NURTURE/QUALIFY are pre-trusted.
- Friday: you get the weekly digest automatically.

## The files you got (what each does)
| File | Role |
|---|---|
| `hopper/gate.py` | Queue + gate engine (next account, status, stage, enroll, approve). Portable. |
| `hopper/digest.py` | Weekly rollup. Portable. |
| `hopper/hopper.jsonl` | Your ranked account queue. |
| `hopper/rep_config.json` | Your identity (Slack, mailbox, sequence). |
| `hopper/apollo_config.json` | Shared Apollo wiring (sequence, custom fields, import spec). |
| `hopper/MORNING_DRIVER.md` | The daily procedure = the scheduled task prompt. |
| `hopper/GATE.md` | Hybrid-by-quadrant gate rules. |
| `hopper/APOLLO_SETUP.md` | One-time custom-field + sequence wiring. |
| `hopper/setup.py` | Scaffolds your workspace (Step 1). |

## Gotchas (learned the hard way)
- **Run now once** or autonomous runs do nothing (Step 6).
- **Insert merge variables via the `{ }` picker**, never hand-type `{{...}}`, or emails send literal tokens.
- **Don't activate** a contact before its import fills the fields, or it sends a blank email.
- Apollo enrollment + activation always need your explicit confirmation — by design.
