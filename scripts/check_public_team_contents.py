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
    text = "".join(kept)
    # Keep the clean-install correction explicit in the baseline comparison.
    previous_start = """./capstone up --mock
```

- 첫 실행 때 비밀값을 생성하고 이미지를 빌드한 뒤 DB 마이그레이션까지 적용합니다. `--mock`을 빼면 자동매매가 꺼진 채로 뜹니다.
- 출력에 `CAPSTONE_UP=PASS`와 `CAPSTONE_AUTOMATION_RECONCILED=ARMED`가 모두 보이면 기동이 끝난 것입니다."""
    current_start = """./capstone up
```

- 첫 실행 때 비밀값을 생성하고 이미지 빌드와 DB 마이그레이션을 진행합니다. `CAPSTONE_UP=PASS`가 표시되면 웹과 API를 열 수 있습니다. 이 실행은 KIS 키 없이 시작하며 자동운용은 꺼져 있습니다.
- KIS 모의계좌를 쓰려면 별도로 계좌 설정과 인증을 마친 뒤 `./capstone up --mock`을 실행합니다. `CAPSTONE_AUTOMATION_RECONCILED=ARMED`는 자동운용 준비 상태입니다."""
    if text.count(previous_start) != 1:
        raise ValueError("baseline README startup instructions are missing or ambiguous")
    return text.replace(previous_start, current_start, 1)


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
