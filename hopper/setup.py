#!/usr/bin/env python3
"""
One-time scaffold for a new rep. Run once after cloning/downloading the toolkit.

Usage:
  python3 hopper/setup.py                          # interactive setup
  python3 hopper/setup.py --auto                   # scaffold only, skip interactive questions

This script:
- Creates state/ and runs/ folders and empty state files.
- Creates rep_config.json from the template if it does not exist.
- Creates apollo_config.json from the template if it does not exist.
- Creates an empty hopper.jsonl if none exists.
- Validates configs and reports what still needs filling.
- Hydrates the Morning Driver prompt with the correct absolute base path.

What it does NOT do (these need Claude + your judgment):
- Score your accounts into the hopper (Claude runs account-scoring).
- Discover your Slack/Apollo IDs (Claude looks them up via MCP tools).
- Register the scheduled tasks (Claude does this via the scheduler).
"""
import json, os, shutil, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    print(f"  dir   {p}")


def ensure_file(p, content=""):
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(content)
        print(f"  file  {p} (created)")
    else:
        print(f"  file  {p} (exists, kept)")


def create_from_template(tmpl, dest, skip_if_exists=True):
    if skip_if_exists and os.path.exists(dest):
        print(f"  file  {dest} (exists, kept)")
        return
    if os.path.exists(tmpl):
        shutil.copy(tmpl, dest)
        print(f"  file  {dest} (created from template)")
    else:
        print(f"  WARN  template not found: {tmpl}")


def validate_json(path, label, required_keys=None):
    print(f"\n=== {label} ===")
    try:
        cfg = json.load(open(path))
        issues = []
        if required_keys:
            for k in required_keys:
                if k not in cfg:
                    issues.append(f"missing: {k}")
                elif isinstance(cfg[k], str) and (cfg[k].strip().startswith("<") or cfg[k].strip().startswith("YOUR_")):
                    issues.append(f"placeholder: {k}")
        else:
            for k, v in cfg.items():
                if isinstance(v, str) and (v.strip().startswith("<") or v.strip().startswith("YOUR_")):
                    issues.append(f"placeholder: {k}")
        if issues:
            print(f"STILL NEEDS FILLING: {', '.join(issues)}")
            return False
        else:
            print("All fields filled.")
            return True
    except FileNotFoundError:
        print(f"File not found: {path}")
        return False
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return False


def migrate_apollo_ids(rep_path, apollo_path):
    """Copy legacy Apollo keys from rep_config.json to apollo_config.json for backwards compatibility."""
    try:
        if not os.path.exists(apollo_path):
            return
        rep_cfg = json.load(open(rep_path))
        apollo_cfg = json.load(open(apollo_path))
        mapping = {
            "apollo_sequence_id": "sequence_id",
            "apollo_sequence_name": "sequence_name",
            "apollo_sender_email_account_id": "sender_email_account_id"
        }
        migrated = False
        for old_key, new_key in mapping.items():
            if old_key in rep_cfg and (new_key not in apollo_cfg or apollo_cfg[new_key].strip().startswith("<") or apollo_cfg[new_key].strip().startswith("YOUR_")):
                apollo_cfg[new_key] = rep_cfg[old_key]
                migrated = True
                print(f"  Migrated {old_key} -> {new_key}")
        if migrated:
            with open(apollo_path, "w") as f:
                json.dump(apollo_cfg, f, indent=2)
                f.write("\n")
            print("Migrated Apollo IDs from rep_config.json to apollo_config.json")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  Could not migrate Apollo IDs: {e}")


def hydrate_morning_driver():
    """Write a team-specific MORNING_DRIVER.md with BASE and placeholders filled."""
    src = f"{HERE}/MORNING_DRIVER.md"
    dest = f"{HERE}/MORNING_DRIVER.md"  # overwrite in place — this is expected
    if not os.path.exists(src):
        return
    with open(src) as f:
        txt = f.read()
    # Only replace the template comment with the actual base path comment
    if "MORNING_DRIVER.md.active" not in txt and "BASE = \"<BASE>\"" in txt:
        txt = txt.replace("BASE = \"<BASE>\"", f'BASE = "{BASE}"')
        with open(dest, "w") as f:
            f.write(txt)
        print(f"  Hydrated BASE path in {dest}")


def main():
    p = argparse.ArgumentParser(description="Scaffold Apollo Pipeline workspace")
    p.add_argument("--auto", action="store_true", help="Non-interactive: scaffold only, skip prompts")
    a = p.parse_args()

    print(f"Scaffolding workspace under: {BASE}\n")
    ensure_dir(f"{BASE}/state")
    ensure_dir(f"{BASE}/runs")
    ensure_file(f"{BASE}/state/active-contacts.jsonl")
    ensure_file(f"{BASE}/state/processed-replies.jsonl")
    ensure_file(f"{BASE}/state/pending-approvals.jsonl")
    ensure_file(f"{BASE}/hopper/hopper.jsonl")

    create_from_template(f"{HERE}/rep_config.template.json", f"{HERE}/rep_config.json")
    create_from_template(f"{HERE}/apollo_config.template.json", f"{HERE}/apollo_config.json")

    print("")
    rep_ok = validate_json(f"{HERE}/rep_config.json", "rep_config.json", required_keys=["rep_name", "rep_email", "slack_user_id"])

    migrate_apollo_ids(f"{HERE}/rep_config.json", f"{HERE}/apollo_config.json")

    apollo_ok = validate_json(f"{HERE}/apollo_config.json", "apollo_config.json", required_keys=["sequence_id", "sequence_name", "sender_email_account_id"])

    n = 0
    hp = f"{BASE}/hopper/hopper.jsonl"
    if os.path.exists(hp):
        n = sum(1 for line in open(hp) if line.strip())
    print(f"\nHopper accounts: {n}")
    if n == 0:
        print("Hopper is empty. Next: have Claude score your accounts into hopper.jsonl.")
        print("  Tip: Create hopper/accounts.jsonl with one JSON object per line, then run:")
        print("       python3 hopper/build_hopper.py")

    print("")
    hydrate_morning_driver()

    print("\nScaffold done.")
    if not rep_ok or not apollo_ok:
        print("\nNext: Fill in rep_config.json and apollo_config.json, then follow TEAM-SETUP.md.")
        print("  Claude can look up your Slack ID (slack_search_users) and Apollo IDs")
        print("  (apollo_email_accounts_index, apollo_emailer_campaigns_search) for you.")
    else:
        print("\nConfigs look complete. Next: register scheduled tasks and run 'Run now' once.")
        print("  See TEAM-SETUP.md steps 5-6.")


if __name__ == "__main__":
    main()
