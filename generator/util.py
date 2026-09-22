"""Small pure-stdlib helpers shared by the generator.

Nothing in here touches the data model; keeping them separate makes the
rendering code readable and the helpers individually testable.
"""

from __future__ import annotations

import datetime as _dt
import html
import json
import pathlib
import re
import unicodedata

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_WS = re.compile(r"\s+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


# --------------------------------------------------------------------------- #
# Text
# --------------------------------------------------------------------------- #
def slugify(value: str) -> str:
    """`"Google Gemini"` -> `"google-gemini"`."""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return _SLUG_STRIP.sub("-", ascii_value.lower()).strip("-")


def esc(value: object) -> str:
    """HTML-escape any value (quotes included) for use in text or attributes."""
    return html.escape(str(value), quote=True)


def collapse_ws(value: str) -> str:
    return _WS.sub(" ", value).strip()


def sentence_count(value: str) -> int:
    return len([s for s in _SENTENCE_SPLIT.split(collapse_ws(value)) if s])


def word_count(value: str) -> int:
    return len(collapse_ws(value).split())


def truncate(value: str, limit: int, suffix: str = "…") -> str:


# --------------------------------------------------------------------------- #
# Dates
# --------------------------------------------------------------------------- #
def today_iso() -> str:
    return _dt.date.today().isoformat()


def parse_date(value: str) -> _dt.date:
    """Parse an ISO `YYYY-MM-DD` date, raising ValueError on anything else."""
    return _dt.datetime.strptime(value, "%Y-%m-%d").date()


def days_since(iso_date: str) -> int:
    return (_dt.date.today() - parse_date(iso_date)).days


def stale_label(iso_date: str, warn_after_days: int = 180) -> str | None:
    """Human-readable warning when a `pricing_last_verified` date is old."""
    age = days_since(iso_date)
    if age < 0:
        return "verification date is in the future"
    if age > warn_after_days:
        return f"not re-verified for ~{max(1, age // 30)} months"
    return None


def launch_sort_key(launched: str) -> tuple[int, int]:
    """`"2022"` / `"2022-11"` / `"2022-11-30"` -> sortable tuple."""
    parts = re.split(r"[-/]", str(launched))
    year = int(parts[0]) if parts and parts[0].isdigit() else 0
    month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    day = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    return (year, month * 100 + day)


# --------------------------------------------------------------------------- #
# Money
# --------------------------------------------------------------------------- #
_MONEY_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]+)?)")
_ANNUAL_RE = re.compile(r"per\s+year|/\s*(?:yr|year)|annually|annual|/\s*mo\s*/\s*yr", re.IGNORECASE)


def parse_monthly_usd(price: str) -> float | None:
    """Best-effort `"$20/user/month"` -> `20.0`, `"$200/year"` -> `16.67`.

    Returns None when nothing numeric can be read so callers can warn instead
    of silently rendering a wrong "from $X" badge.
    """
    match = _MONEY_RE.search(price)
    if not match:
        return None
    amount = float(match.group(1))
    return round(amount / 12, 2) if _ANNUAL_RE.search(price) else amount


def format_usd(amount: float) -> str:
    return f"${amount:,.0f}" if amount % 1 == 0 else f"${amount:,.2f}".rstrip("0").rstrip(".")

    value = collapse_ws(value)
    return value if len(value) <= limit else value[: limit - len(suffix)].rstrip() + suffix


def monogram(name: str) -> str:
    """`"Microsoft 365 Copilot"` -> `"M"`. Used when no logo asset is available.


# --------------------------------------------------------------------------- #
# JSON / filesystem
# --------------------------------------------------------------------------- #
def read_json(path: pathlib.Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dumps(data: object, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def write_json(path: pathlib.Path, data: object, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(data, compact=compact) + "\n", encoding="utf-8")


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
def page_url(*segments: str) -> str:
    """Root-absolute URL for a generated page, e.g. `/tools/chatgpt/`.

    Every page is a directory containing `index.html`: clean URLs, works when
    served from GitHub Pages, works when opened straight off disk.
    """
    cleaned = [slugify(s) for s in segments if s]
    return "/" + "/".join(cleaned) + "/" if cleaned else "/"


class Linker:
    """Rewrites root-absolute hrefs for a page nested `depth` levels deep.

    Using relative hrefs means the same build works at a domain root, on a
    GitHub Pages project sub-path (`/learners.ai/...`) and from `file://`.
    """

    __slots__ = ("depth",)

    def __init__(self, depth: int = 0) -> None:
        self.depth = max(0, int(depth))

    def __call__(self, target: str) -> str:
        if not target.startswith("/"):
            return target
        path = target.lstrip("/")
        if self.depth == 0:
            return path or "./"
        return "../" * self.depth + path


    A single letter reads better than two-letter initials in a small badge and
    avoids collisions between products from the same maker.
    """
    cleaned = re.sub(r"[^A-Za-z0-9 ]", " ", name).strip()
    return cleaned[0].upper() if cleaned else "?"
