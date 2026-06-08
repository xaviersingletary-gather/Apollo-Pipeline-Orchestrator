#!/usr/bin/env python3
"""
One-time scaffold for a new rep. Run once after copying the toolkit folder.

What it does (mechanical only, safe to re-run):
- Creates state/ and runs/ folders and empty state files.
- Creates rep_config.json from the template if it does not exist.
- Creates an empty hopper.jsonl if none exists.
- Validates rep_config.json and reports what still needs filling.

What it does NOT do (these need Claude + your judgment, see TEAM-SETUP.md):
- Score your accounts into the hopper (Claude runs account-scoring).
- Discover your Slack/Apollo IDs (Claude looks them up).
- Register the scheduled tasks (Claude does this via the scheduler).

Usage: python3 setup.py
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True); print(f"  dir   {p}")

def ensure_file(p, content=""):
    if not os.path.exists(p):
        with open(p, "w") as f: f.write(content)
        print(f"  file  {p} (created)")
    else:
        print(f"  file  {p} (exists, kept)")

print("Scaffolding rep workspace under:", BASE)
ensure_dir(f"{BASE}/state")
ensure_dir(f"{BASE}/runs")
ensure_file(f"{BASE}/state/active-contacts.jsonl")
ensure_file(f"{BASE}/state/processed-replies.jsonl")
ensure_file(f"{BASE}/state/pending-approvals.jsonl")
ensure_file(f"{BASE}/hopper/hopper.jsonl")

cfg_path = f"{HERE}/rep_config.json"
tmpl_path = f"{HERE}/rep_config.template.json"
if not os.path.exists(cfg_path):
    if os.path.exists(tmpl_path):
        shutil.copy(tmpl_path, cfg_path)
        print(f"  file  {cfg_path} (created from template — FILL IT IN)")
else:
    print(f"  file  {cfg_path} (exists, kept)")

print("\n=== rep_config.json status ===")
try:
    cfg = json.load(open(cfg_path))
    missing = [k for k, v in cfg.items() if isinstance(v, str) and v.strip().startswith("<")]
    if missing:
        print("STILL NEEDS FILLING:", ", ".join(missing))
    else:
        print("All identity fields filled.")
except Exception as e:
    print("Could not read rep_config.json:", e)

n = 0
hp = f"{BASE}/hopper/hopper.jsonl"
if os.path.exists(hp):
    n = sum(1 for line in open(hp) if line.strip())
print(f"\nHopper accounts: {n}")
if n == 0:
    print("Hopper is empty. Next: have Claude score your accounts into hopper.jsonl (see TEAM-SETUP.md step 3).")

print("\nScaffold done. Now follow TEAM-SETUP.md (steps 2-6) with Claude.")
