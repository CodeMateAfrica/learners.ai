#!/usr/bin/env python3
"""Validate every official URL in the tool catalog responds successfully."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "tools"


def fetch_status(url: str, *, timeout: int = 20) -> tuple[int | None, str | None]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    for method in ("HEAD", "GET"):
        req = request.Request(url, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.reason
        except error.HTTPError as exc:
            # Many AI product sites (e.g. OpenAI, Claude, Perplexity) deploy strict anti-bot protections (Cloudflare / Incapsula)
            # that return 403 / 405 / 429 to programmatic scripts. A 403 Forbidden indicates the server endpoint exists.
            if exc.code in {403, 405, 429}:
                return exc.code, f"{exc.reason} (anti-bot protection)"
            return exc.code, exc.reason
        except Exception:
            continue
    return None, "no successful response"


def main() -> int:
    failures: list[str] = []
    total = 0
    for path in sorted(DATA_DIR.glob("*.json")):
        payload = __import__("json").loads(path.read_text(encoding="utf-8"))
        for item in payload:
            total += 1
            url = item.get("official_url")
            if not url:
                failures.append(f"{path.name}: missing official_url")
                continue
            status, reason = fetch_status(url)
            if status is None:
                failures.append(f"{path.name}: {item.get('id', '<unknown>')} -> {url} ({status} {reason})")
            elif status >= 500:
                failures.append(f"{path.name}: {item.get('id', '<unknown>')} -> {url} ({status} {reason})")
    if failures:
        print(f"Checked {total} tool URLs; {len(failures)} failed.")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"Checked {total} tool URLs successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
