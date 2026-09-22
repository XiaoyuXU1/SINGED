#!/usr/bin/env python3
"""Fail if the release contains secrets, personal paths, or generated artifacts."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENY = {
    "local user path": re.compile(r"/(?:Users|home)/[^/\s]+", re.IGNORECASE),
    "cloud-sync path": re.compile(r"OneDrive|Dropbox|iCloud", re.IGNORECASE),
    "messaging identifier": re.compile(r"wxid_[a-z0-9]+", re.IGNORECASE),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenRouter key": re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    "generic secret assignment": re.compile(r"(?i)(?:api[_-]?key|token|secret)\s*[=:]\s*['\"][^'\"]{12,}['\"]"),
}
PRIVATE_TERMS = [term.strip() for term in os.environ.get("SINGED_PRIVATE_TERMS", "").split(",") if term.strip()]
PERSONAL = re.compile("|".join(re.escape(term) for term in PRIVATE_TERMS), re.IGNORECASE) if PRIVATE_TERMS else None


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True)
    return [ROOT / line for line in output.splitlines() if line]


def main() -> None:
    findings: list[str] = []
    for path in tracked_files():
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        if relative == Path("scripts/check_release.py"):
            continue
        if PERSONAL and PERSONAL.search(text):
            findings.append(f"{relative}: personal identifier")
        for label, pattern in DENY.items():
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if findings:
        raise SystemExit("release check failed:\n" + "\n".join(sorted(set(findings))))
    print(f"release check passed: {len(tracked_files())} files scanned")


if __name__ == "__main__":
    main()
