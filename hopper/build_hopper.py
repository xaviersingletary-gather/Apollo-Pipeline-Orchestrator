"""
Build Fit x Signal triage + machine-readable hopper for the self-driving Apollo pipeline.
Same scoring method and xlsx format as the reference triage (account-scoring skill, Fit x Signal v1).

Usage:
  python3 hopper/build_hopper.py                    # reads hopper/accounts.jsonl
  python3 hopper/build_hopper.py accounts.jsonl     # reads from provided file

The accounts file should be JSONL with one account per line:
  {"name": "Walmart", "domain": "walmart.com", "fit": [10,10,10,9], "sig": [9,8,7,9,8], "conf": "H", "anchor": "...", "move": "..."}

Scoring rules (verdict):
  STRIKE = Fit>=70 AND Signal>=70
  NURTURE = Fit>=70 AND Signal<70
  QUALIFY = Fit 40-69, Signal>=40
  KILL = either <40
"""
import json, os, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

# Default: look for hopper/accounts.jsonl, else hopper/accounts.json
ACCOUNTS_FILE = os.environ.get("ACCOUNTS_FILE", f"{HERE}/accounts.jsonl")
HOPPER_FILE = f"{HERE}/hopper.jsonl"


def axis(scores):
    return round(sum(scores) / len(scores) * 10, 1)


def compute_verdict(fit, sig):
    if fit < 40 or sig < 40:
        return "KILL"
    if fit >= 70 and sig >= 70:
        return "STRIKE"
    if fit >= 70 and sig < 70:
        return "NURTURE"
    return "QUALIFY"


def load_accounts(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def score_accounts(accounts):
    for a in accounts:
        a["fit_score"] = axis(a["fit"])
        a["sig_score"] = axis(a["sig"])
        a["verdict"] = compute_verdict(a["fit_score"], a["sig_score"])
    order_rank = {"STRIKE": 0, "NURTURE": 1, "QUALIFY": 2, "KILL": 3}
    accounts.sort(key=lambda a: (order_rank[a["verdict"]], -(a["fit_score"] + a["sig_score"])))
    return accounts


def write_hopper(accounts):
    today = date.today().isoformat()
    with open(HOPPER_FILE, "w") as f:
        for rank, a in enumerate(accounts, 1):
            rec = {
                "rank": rank,
                "account": a["name"],
                "domain": a["domain"],
                "verdict": a["verdict"],
                "fit": a["fit_score"],
                "signal": a["sig_score"],
                "confidence": a.get("conf", "M"),
                "top_move": a.get("move", ""),
                "status": "todo",
                "last_worked_at": None,
                "sequence_target": None,
                "scored_at": today,
            }
            f.write(json.dumps(rec) + "\n")
    print(f"Saved hopper: {HOPPER_FILE}")
    for v in ["STRIKE", "NURTURE", "QUALIFY", "KILL"]:
        matches = [f"{a['name']} ({a['fit_score']}/{a['sig_score']})" for a in accounts if a["verdict"] == v]
        print(f"  {v} ({len(matches)}): {', '.join(matches) if matches else '-'}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build hopper from accounts JSONL")
    ap.add_argument("accounts_file", nargs="?", default=ACCOUNTS_FILE, help="Path to accounts JSONL")
    a = ap.parse_args()

    accounts = load_accounts(a.accounts_file)
    if not accounts:
        print(f"No accounts found at {a.accounts_file}")
        print("Create the accounts file (one JSONL line per account, see docstring) then re-run.")
        sys.exit(1)

    accounts = score_accounts(accounts)
    write_hopper(accounts)


if __name__ == "__main__":
    main()
