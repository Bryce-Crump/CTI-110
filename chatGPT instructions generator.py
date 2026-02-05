#!/usr/bin/env python3
# Alignment Checklist CLI (local-friendly, v3)
# Default output directory: ~/Downloads (created if missing). Override with --out PATH.
# If ~/Downloads cannot be determined, falls back to current working directory.
#
# Includes v2 questions:
# - assumptions_allowed (yes/no; default no)
# - authoritative_source_preference (upstream docs/distro docs/vendor docs; default vendor docs)
# - rollback_required (yes/no; default yes)
# - statefulness (ephemeral/persistent; default persistent)

import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path

def default_downloads_dir() -> Path:
    # Cross-platform guess for Downloads
    home = Path.home()
    cand = home / "Downloads"
    try:
        cand.mkdir(parents=True, exist_ok=True)
        return cand
    except Exception:
        return Path.cwd()

def ask(prompt, required=True, default=None):
    while True:
        suffix = f" [default: {default}] " if default is not None else " "
        try:
            val = input(prompt.strip() + suffix).strip()
        except EOFError:
            val = ""
        if not val and default is not None:
            return default
        if val or not required:
            return val
        print("This field is required.")

def ask_choice(prompt, choices, default=None, required=True):
    norm = {c.lower(): c for c in choices}
    disp = "/".join(choices)
    while True:
        raw = ask(f"{prompt} ({disp})", required=required, default=default)
        val = raw.lower()
        if val in norm:
            return norm[val]
        if set(map(str.lower, choices)) == {"yes","no"}:
            if val in ("y","yes"): return "yes"
            if val in ("n","no"): return "no"
        print(f"Please choose one of: {disp}")

def main():
    parser = argparse.ArgumentParser(description="Alignment Checklist (project brief generator)")
    parser.add_argument("--out", default=None, help="Output directory (default: ~/Downloads)")
    args = parser.parse_args()

    out_dir = Path(args.out).expanduser().resolve() if args.out else default_downloads_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== Alignment Checklist ===")
    brief = {}
    brief["service_name_version"] = ask("Service to set up (exact name + version):")
    brief["environment_location"] = ask("Where is it being set up? (cloud/vm/bare metal + provider/region + OS/distro + version/arch):")
    brief["programs_involved"] = ask("Programs/packages/daemons involved (exact versions if possible):")
    brief["desired_outcome"] = ask("Desired outcome (business + technical, success criteria):")
    brief["constraints"] = ask("Constraints (e.g., offline repo only, FIPS, specific ports):", required=False)
    brief["timeline_urgency"] = ask("Urgency/timebox (e.g., 20 minutes, same-day, this week):", required=False, default="timebox: 20 minutes")
    brief["security_compliance"] = ask("Security/compliance needs (e.g., CIS level, logging retention):", required=False)
    brief["change_control"] = ask("Change ticket/approval id (if any):", required=False)

    brief["assumptions_allowed"] = ask_choice("Assumptions allowed", ["yes","no"], default="no")
    brief["authoritative_source_preference"] = ask_choice("Authoritative source preference", ["upstream docs","distro docs","vendor docs"], default="vendor docs")
    brief["rollback_required"] = ask_choice("Rollback required", ["yes","no"], default="yes")
    brief["statefulness"] = ask_choice("Statefulness", ["ephemeral","persistent"], default="persistent")

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    brief["created_utc"] = ts

    md_lines = ["# Project Brief (Lock Scope Before Execution)", ""]
    ordered_keys = [
        "service_name_version","environment_location","programs_involved","desired_outcome",
        "constraints","timeline_urgency","security_compliance","change_control",
        "assumptions_allowed","authoritative_source_preference","rollback_required","statefulness",
        "created_utc"
    ]
    for k in ordered_keys:
        md_lines.append(f"- **{k.replace('_',' ').title()}**: {brief.get(k,'')}")
    md_lines.append("")
    md_lines.append("> Paste the above into chat to confirm scope. The assistant will then provide ONLY environment-specific steps.")

    md_path = out_dir / "project-brief.md"
    json_path = out_dir / "project-brief.json"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)

    print("\n".join(md_lines))
    print(f"\nSaved to: {out_dir}")
    print(str(md_path))
    print(str(json_path))

if __name__ == "__main__":
    try:
        main()
    except PermissionError as e:
        print(f"Permission error: {e}. Try a writable --out directory.")
        raise
