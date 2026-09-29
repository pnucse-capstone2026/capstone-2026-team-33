#!/usr/bin/env python3
"""Check the public team repository's documentation allowlist and README baseline."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_BASELINE_COMMIT = "a502be4"
FORBIDDEN_PATHS = (
    "docs/adr",
    "docs/screenshots",
    "docs/API_명세서.md",
    "docs/FULL_상태전이_DB_검증표.md",
    "docs/KIS_API_카탈로그.md",
    "docs/README.md",
    "docs/금융공학_공식_및_자동매매_로직_설명서.md",
    "docs/최종_프로젝트_명세서.md",
)
PUBLIC_DOCS = {
    "docs/01.보고서/03.최종보고서.docx",
    "docs/01.보고서/03.최종보고서.pdf",
    "docs/03.발표자료/발표자료.pptx",
    "docs/04.자문의견서/자문의견서.pdf",
}
README_MARKERS_TO_REMOVE = tuple(FORBIDDEN_PATHS[2:])


def fail(message: str) -> int:
    print(f"PUBLIC_REPOSITORY_CONTENT_POLICY=FAIL: {message}", file=sys.stderr)
    return 1


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return completed.stdout


def expected_public_readme() -> str:
    source = git("show", f"{README_BASELINE_COMMIT}:README.md")
    kept: list[str] = []
    in_screenshot_table = False
    for line in source.splitlines(keepends=True):
        if in_screenshot_table:
            if "docs/screenshots/backtest.png" in line:
                in_screenshot_table = False
            continue
        if "| 자동운용 | 주문 검토 |" in line:
            in_screenshot_table = True
            continue
        if any(marker in line for marker in README_MARKERS_TO_REMOVE):
            continue
        kept.append(line)
    if in_screenshot_table:
        raise ValueError("baseline README screenshot table has no closing row")
    return "".join(kept)


def main() -> int:
    for relative in FORBIDDEN_PATHS:
        if os.path.lexists(ROOT / relative):
            return fail(f"forbidden public path exists: {relative}")

    tracked_docs = set(git("-c", "core.quotePath=false", "ls-files", "--", "docs").splitlines())
    if tracked_docs != PUBLIC_DOCS:
        return fail(
            f"docs/ must contain only approved public materials; found {sorted(tracked_docs)}"
        )
    for relative in PUBLIC_DOCS:
        target = ROOT / relative
        if not target.is_file() or target.stat().st_size == 0:
            return fail(f"public report material is missing or empty: {relative}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if readme != expected_public_readme():
        return fail(
            f"README.md drifted from {README_BASELINE_COMMIT} minus internal links and screenshots; update the baseline intentionally"
        )
    for relative in ("README.md", "CONTRIBUTING.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in FORBIDDEN_PATHS:
            if marker in text:
                return fail(f"{relative} links to or names removed documentation: {marker}")

    print("PUBLIC_REPOSITORY_CONTENT_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
