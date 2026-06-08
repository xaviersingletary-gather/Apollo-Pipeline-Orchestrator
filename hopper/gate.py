#!/usr/bin/env python3
"""
Hybrid-by-quadrant gate + enrollment adapter for the self-driving Apollo pipeline.

The Morning Driver (and any manual run) calls this for deterministic decisions so
behavior stays identical across daily fires and across teammates.

Gate rule (Peter's choice):
  STRIKE             -> "approve"  (stage + Slack Peter, enroll only on his yes)
  NURTURE / QUALIFY  -> "auto"     (enroll immediately)
  KILL / IGNORE      -> "skip"

Enrollment adapter:
  --mode csv     (default today) : log contacts to watcher state, flag CSV cleared-to-upload
  --mode apollo  (when connected): enroll via Apollo MCP. Stub for now, raises until wired.

CLI:
  gate.py status                         summary of the hopper queue
  gate.py next                           next account to work (top todo) + gate decision
  gate.py gate <VERDICT>                 -> approve | auto | skip
  gate.py set <account> <status> [--sequence ID] [--worked]
  gate.py stage <account> <csv_path>     STRIKE: mark staged_for_approval, record pending
  gate.py pending                        list runs awaiting Peter's approval
  gate.py approve <account>              approve a staged STRIKE -> enroll in current mode
  gate.py enroll <account> <csv_path> [--mode csv|apollo] [--sequence ID]

Statuses: todo -> in_progress -> staged_for_approval -> enrolled -> done | parked
"""
import argparse, json, os, sys, csv as csvmod
from datetime import datetime, timezone

# Portable: BASE is the Apollo Pipeline Orchestrator dir (parent of this hopper/ folder),
# derived from this script's own location so the toolkit works wherever it's copied.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOPPER = f"{BASE}/hopper/hopper.jsonl"
STATE = f"{BASE}/state"
ACTIVE = f"{STATE}/active-contacts.jsonl"
PENDING = f"{STATE}/pending-approvals.jsonl"

GATE = {"STRIKE": "approve", "NURTURE": "auto", "QUALIFY": "auto", "KILL": "skip"}
WORK_STATUSES = {"todo"}

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    rows = []
    with open(HOPPER) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def save(rows):
    rows.sort(key=lambda r: r.get("rank", 999))
    with open(HOPPER, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

def find(rows, account):
    acct = account.lower()
    for r in rows:
        if r["account"].lower() == acct or r["account"].lower().startswith(acct):
            return r
    return None

def needs_research(r):
    # L-confidence accounts must get a fresh account-research pass before working.
    return r.get("confidence") == "L"

def cmd_status(_):
    rows = load()
    by_status, by_verdict = {}, {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
    todo = [r for r in rows if r["status"] in WORK_STATUSES]
    print("=== HOPPER STATUS ===")
    print("By status :", by_status)
    print("By verdict:", by_verdict)
    print(f"\nWork queue (top todo, {len(todo)} left):")
    for r in todo:
        flag = "  [needs research]" if needs_research(r) else ""
        print(f"  #{r['rank']:>2} {r['account']:<26} {r['verdict']:<8} {r['fit']}/{r['signal']} ({r['confidence']}) -> {GATE[r['verdict']]}{flag}")

def cmd_next(_):
    rows = load()
    todo = [r for r in rows if r["status"] in WORK_STATUSES]
    if not todo:
        print(json.dumps({"empty": True, "message": "Hopper has no todo accounts. Trigger low-hopper watchdog."}))
        return
    r = todo[0]
    out = {
        "account": r["account"], "domain": r["domain"], "verdict": r["verdict"],
        "fit": r["fit"], "signal": r["signal"], "confidence": r["confidence"],
        "gate": GATE[r["verdict"]], "needs_research": needs_research(r),
        "top_move": r["top_move"], "remaining_todo": len(todo),
    }
    print(json.dumps(out, indent=2))

def cmd_gate(a):
    print(GATE.get(a.verdict.upper(), "skip"))

def cmd_set(a):
    rows = load()
    r = find(rows, a.account)
    if not r:
        sys.exit(f"Account not found: {a.account}")
    r["status"] = a.status
    if a.sequence:
        r["sequence_target"] = a.sequence
    if a.worked:
        r["last_worked_at"] = now()
    save(rows)
    print(f"{r['account']} -> status={a.status}" + (f", sequence={a.sequence}" if a.sequence else ""))

def cmd_stage(a):
    rows = load()
    r = find(rows, a.account)
    if not r:
        sys.exit(f"Account not found: {a.account}")
    if not os.path.exists(a.csv_path):
        sys.exit(f"CSV not found: {a.csv_path}")
    r["status"] = "staged_for_approval"
    r["last_worked_at"] = now()
    save(rows)
    os.makedirs(STATE, exist_ok=True)
    with open(a.csv_path, newline="") as cf:
        n = sum(1 for _ in csvmod.DictReader(cf))
    with open(PENDING, "a") as f:
        f.write(json.dumps({"account": r["account"], "verdict": r["verdict"],
                            "csv_path": a.csv_path, "contacts": n, "staged_at": now()}) + "\n")
    print(f"STAGED {r['account']} ({n} contacts) for approval. Awaiting Peter's yes.")

def cmd_pending(_):
    if not os.path.exists(PENDING):
        print("No pending approvals.")
        return
    seen = {}
    for line in open(PENDING):
        line = line.strip()
        if line:
            rec = json.loads(line)
            seen[rec["account"]] = rec  # last entry wins
    # only those still staged in hopper
    rows = {r["account"]: r for r in load()}
    open_items = [v for k, v in seen.items() if rows.get(k, {}).get("status") == "staged_for_approval"]
    if not open_items:
        print("No pending approvals.")
        return
    print("=== PENDING APPROVAL (STRIKE) ===")
    for rec in open_items:
        print(f"  {rec['account']:<26} {rec['contacts']} contacts  staged {rec['staged_at'][:16]}  csv: {rec['csv_path']}")

def _log_active(csv_path, company, sequence_id):
    os.makedirs(STATE, exist_ok=True)
    added = 0
    with open(csv_path, newline="") as f, open(ACTIVE, "a") as out:
        for row in csvmod.DictReader(f):
            email = (row.get("email") or "").strip()
            if not email:
                continue
            out.write(json.dumps({
                "email": email,
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "company": row.get("company", company),
                "sequence_id": sequence_id or "CSV-PENDING",
                "enrolled_at": now(),
            }) + "\n")
            added += 1
    return added

def _enroll(account, csv_path, mode, sequence):
    # Both modes record watcher state from the run CSV.
    # apollo mode: the Driver/Claude session has ALREADY performed the MCP enrollment
    #   (apollo_contacts_bulk_create -> apollo_emailer_campaigns_add_contact_ids, paused).
    #   gate.py only records it here. MCP tools are not callable from this subprocess.
    # csv mode: interim fallback. CSV is cleared for manual Apollo upload.
    n = _log_active(csv_path, account, sequence)
    return n

def cmd_enroll(a):
    rows = load()
    r = find(rows, a.account)
    if not r:
        sys.exit(f"Account not found: {a.account}")
    n = _enroll(r["account"], a.csv_path, a.mode, a.sequence)
    r["status"] = "enrolled"
    r["last_worked_at"] = now()
    if a.sequence:
        r["sequence_target"] = a.sequence
    save(rows)
    print(f"ENROLLED {r['account']} ({n} contacts -> watcher state). Mode={a.mode}. "
          f"{'CSV cleared for manual Apollo upload: ' + a.csv_path if a.mode=='csv' else ''}")

def cmd_approve(a):
    rows = load()
    r = find(rows, a.account)
    if not r:
        sys.exit(f"Account not found: {a.account}")
    if r["status"] != "staged_for_approval":
        sys.exit(f"{r['account']} is not staged_for_approval (status={r['status']}).")
    # locate csv from pending record
    csv_path = None
    if os.path.exists(PENDING):
        for line in open(PENDING):
            line = line.strip()
            if line:
                rec = json.loads(line)
                if rec["account"] == r["account"]:
                    csv_path = rec["csv_path"]
    if not csv_path or not os.path.exists(csv_path):
        sys.exit(f"Could not find staged CSV for {r['account']}.")
    n = _enroll(r["account"], csv_path, a.mode, a.sequence)
    r["status"] = "enrolled"
    r["last_worked_at"] = now()
    if a.sequence:
        r["sequence_target"] = a.sequence
    save(rows)
    print(f"APPROVED + ENROLLED {r['account']} ({n} contacts). Mode={a.mode}. "
          f"{'Upload CSV to Apollo: ' + csv_path if a.mode=='csv' else ''}")

def main():
    p = argparse.ArgumentParser(description="Hybrid-by-quadrant gate + enrollment adapter")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("next").set_defaults(fn=cmd_next)
    g = sub.add_parser("gate"); g.add_argument("verdict"); g.set_defaults(fn=cmd_gate)
    s = sub.add_parser("set"); s.add_argument("account"); s.add_argument("status")
    s.add_argument("--sequence"); s.add_argument("--worked", action="store_true"); s.set_defaults(fn=cmd_set)
    st = sub.add_parser("stage"); st.add_argument("account"); st.add_argument("csv_path"); st.set_defaults(fn=cmd_stage)
    sub.add_parser("pending").set_defaults(fn=cmd_pending)
    ap = sub.add_parser("approve"); ap.add_argument("account")
    ap.add_argument("--mode", default="csv", choices=["csv", "apollo"]); ap.add_argument("--sequence"); ap.set_defaults(fn=cmd_approve)
    en = sub.add_parser("enroll"); en.add_argument("account"); en.add_argument("csv_path")
    en.add_argument("--mode", default="csv", choices=["csv", "apollo"]); en.add_argument("--sequence"); en.set_defaults(fn=cmd_enroll)
    a = p.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()
