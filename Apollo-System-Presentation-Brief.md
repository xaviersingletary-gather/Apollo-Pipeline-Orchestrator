# Self-Driving Apollo Pipeline — Presentation Brief

Feed this to CoWork to generate the deck. Each section is one slide. Suggested title:
"The Self-Driving Outbound System: How We Run the Patch on Autopilot."

---

## Slide 1 — Title
**The Self-Driving Outbound System**
One command builds pipeline across the patch every morning. Built on Apollo, Clay, Gmail, and Slack.
Subtitle: From manual prospecting to a scored hopper that works itself.

## Slide 2 — The problem we solved
- Prospecting was manual and I had to babysit it to be sure it ran on time.
- Account selection, research, contact finding, and writing happened by hand, one account at a time.
- No single view of what was worked, what landed, or what was next.

## Slide 3 — What we built
A system that every weekday morning:
1. Pulls the top-scored account off a ranked hopper
2. Researches it, finds and enriches the right contacts
3. Writes a personalized email and call/video script per contact
4. Loads it into Apollo and reports to me in Slack
It raises its hand when the hopper runs low. I stop watching the tool.

## Slide 4 — The scoring hopper
- All assigned accounts scored on the Fit x Signal matrix (4 fit dimensions, 5 signal dimensions).
- Verdicts: STRIKE, NURTURE, QUALIFY, KILL. STRIKE = Fit 70+ and Signal 70+.
- The hopper is the queue. Top of the list gets worked first.
- Today: 11 accounts scored. 3 STRIKE (Walmart, DHL, Sysco), 6 NURTURE, 2 QUALIFY.

## Slide 5 — The daily run (fully automated)
Every weekday 7am the system does this with no input from me:
- Picks the top unworked account
- Pulls or refreshes deep research
- Sources ICP contacts (VP/Director Operations, Supply Chain, Logistics) and enriches verified emails
- Writes a bespoke email, a 30 to 45 second script (call opener plus LinkedIn video), and a connection note per contact
- Creates the contacts in Apollo and fills each one's personalized fields
- Stages the account and Slacks me a one-screen report

## Slide 6 — Smart gating by account tier
Hybrid model so high-value logos get a human touch and the rest move fast:
- STRIKE: I review the content, then approve. Nothing ships without my eyes.
- NURTURE and QUALIFY: content is pre-trusted, one tap to enroll.
- Every account is prepped automatically. I only make the call on whether and when to send.

## Slide 7 — The Apollo multichannel cadence
Each contact runs an 8-day, multi-touch play:
- Day 1: personalized email, call, LinkedIn connection request
- Day 3: call
- Day 5: LinkedIn video
- Day 7: follow-up email
- Day 8: call
The email, call opener, video script, and connection note are all written per contact and loaded automatically.

## Slide 8 — What is automated vs what I do
Automated end to end:
- Account selection, research, contact sourcing and enrichment, content writing, Apollo contact creation, per-contact field population, staging, and all reporting.
Two taps per account (by design and by Apollo's rules):
- Confirm enroll, then activate. These are my no-spam gates.
The human touches stay human: sending the first email, the calls, and the LinkedIn video. That is the point of a rep-led play.

## Slide 9 — I always know what is happening
- A Slack report after every morning run: what was prepped, what is staged, queue depth.
- A low-hopper alert when unworked accounts drop below 3.
- A weekly digest: accounts worked, contacts enrolled, replies by type.
- A response watcher reads my inbox every 15 minutes, scores replies, and pings me.

## Slide 10 — Built to repeat and to share
- The same engine runs on any account. The hopper is just a list.
- Scoring rules, voice rules, and the cadence are codified, not in my head.
- The next step is to package it per rep so the team runs the same motion as themselves.

## Slide 11 — Status and what is next
Proven today:
- 11 accounts scored. DHL run end to end: 6 DHL Supply Chain leaders sourced, enriched, written, and loaded into Apollo (paused for review).
- Daily driver and weekly digest live and scheduled.
Next:
- Finish the Apollo auto-fill via API so there is zero manual data entry.
- Roll the system out to the team, each rep on their own patch.

## Closing line
We turned outbound from a daily chore into a system that runs itself and asks for me only when it matters.
