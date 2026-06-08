#!/usr/bin/env python3
"""
Observability rollup for the self-driving Apollo pipeline.
Reads hopper + run logs + watcher state and prints a glanceable weekly digest
(also used as the Slack body for the apollo-weekly-digest scheduled task).

Usage: python3 digest.py [--days 7]
"""
import argparse, json, os, re, glob
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOPPER = f"{BASE}/hopper/hopper.jsonl"
RUNS = f"{BASE}/runs"
ACTIVE = f"{BASE}/state/active-contacts.jsonl"
REPLIES = f"{BASE}/state/processed-replies.jsonl"

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def within(iso_str, cutoff):
    if not iso_str:
        return False
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=a.days)

    hopper = read_jsonl(HOPPER)
    by_status, by_verdict = {}, {}
    for r in hopper:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
    todo = [r for r in hopper if r["status"] == "todo"]
    staged = [r for r in hopper if r["status"] == "staged_for_approval"]
    enrolled = [r for r in hopper if r["status"] == "enrolled"]

    # runs this week (filename pattern YYYY-MM-DD-...)
    run_files = sorted(glob.glob(f"{RUNS}/*.md"))
    recent_runs = []
    for f in run_files:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f))
        if m:
            try:
                d = datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
                if d >= cutoff:
                    recent_runs.append(os.path.basename(f))
            except ValueError:
                pass

    active = read_jsonl(ACTIVE)
    active_week = [c for c in active if within(c.get("enrolled_at"), cutoff)]

    replies = read_jsonl(REPLIES)
    reply_week = [r for r in replies if within(r.get("processed_at"), cutoff)]
    rc = {"real": 0, "ooo": 0, "wrong_person": 0}
    for r in reply_week:
        rc[r.get("classification", "real")] = rc.get(r.get("classification", "real"), 0) + 1

    low = len(todo) < 3

    lines = []
    lines.append(f"Apollo weekly digest — last {a.days} days")
    lines.append("")
    lines.append(f"Runs fired: {len(recent_runs)}")
    lines.append(f"Accounts staged for your approval: {len(staged)}" + (f" ({', '.join(s['account'] for s in staged)})" if staged else ""))
    lines.append(f"Accounts enrolled: {len(enrolled)}" + (f" ({', '.join(e['account'] for e in enrolled)})" if enrolled else ""))
    lines.append(f"Contacts enrolled this week: {len(active_week)} (all-time {len(active)})")
    lines.append(f"Replies this week: {len(reply_week)}  (real {rc['real']}, OOO {rc['ooo']}, wrong-person {rc['wrong_person']})")
    lines.append("")
    lines.append(f"Hopper: {len(todo)} todo left" + ("  |  REPLENISH: low, re-score soon" if low else ""))
    lines.append(f"  by status: {by_status}")
    if todo:
        nxt = todo[0]
        lines.append(f"  next up: {nxt['account']} ({nxt['verdict']} {nxt['fit']}/{nxt['signal']})")
    if staged:
        lines.append("")
        lines.append("Waiting on you:")
        for s in staged:
            lines.append(f"  approve {s['account']}: gate.py approve \"{s['account']}\"")

    print("\n".join(lines))

if __name__ == "__main__":
    main()
