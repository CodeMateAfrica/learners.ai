"""Strict schema for `data/tools/*.json` tool entries.

The rules here are the contract described in the project brief: every tool
carries the same required fields, every category/role/platform reference must
resolve, and pricing dates must be real ISO dates. Validation collects *all*
problems and reports them at once so a contributor fixing data never plays
whack-a-mole.

Errors fail the build. Warnings (`--strict` promotes them) are style and
freshness nudges that a maintainer should look at but that do not block a site
from being generated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from . import util

# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #

#: Badge taxonomy shown on cards. `open_source` is split out from `free`
#: because the maintenance story differs completely: the software is free
#: forever but the reader usually pays a model provider per token.
PRICING_MODELS: dict[str, dict[str, str]] = {
    "free": {"label": "Free", "slug": "free"},
    "open_source": {"label": "Open source", "slug": "open-source"},
    "freemium": {"label": "Freemium", "slug": "freemium"},
    "paid": {"label": "Paid", "slug": "paid"},
    "enterprise": {"label": "Enterprise", "slug": "enterprise"},
}

_ID_RE = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")
_LAUNCHED_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
_URL_RE = re.compile(r"^https://[^\s/]+(?:\.[^\s/]+)+(?:[/?#]\S*)?$")

#: Marketing filler that must not survive into original writing.
_CLICHES = (
    "cutting-edge",
    "state-of-the-art",
    "revolutionary",
    "game-chang",
    "seamlessly",
    "unlock the power",
    "supercharge",
    "best-in-class",
    "empower",
    "world-class",
    "next-generation",
    "leverage the power",
)


class SchemaError(Exception):
    """Raised when one or more tool entries fail validation."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__(f"{len(problems)} data problem(s) found")


# --------------------------------------------------------------------------- #
# Pricing
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class PaidPlan:
    name: str
    price: str
    notes: str = ""
    usd_monthly: float | None = None  # per-seat monthly equivalent, for sorting

    @property
    def monthly_amount(self) -> float | None:
        if self.usd_monthly is not None:
            return self.usd_monthly
        return util.parse_monthly_usd(self.price)


@dataclass(slots=True)
class Pricing:
    model: str
    has_free_tier: bool
    free_tier_details: str
    paid_plans: list[PaidPlan]
    pricing_last_verified: str
    pricing_url: str = ""
    notes: str = ""

    @property
    def badge_label(self) -> str:
        return PRICING_MODELS[self.model]["label"]

    @property
    def badge_slug(self) -> str:
        return PRICING_MODELS[self.model]["slug"]

    @property
    def cheapest_paid(self) -> PaidPlan | None:
        """Lowest monthly-equivalent plan, ignoring "contact sales" entries."""
        priced = [p for p in self.paid_plans if p.monthly_amount is not None]
        return min(priced, key=lambda p: p.monthly_amount or 0) if priced else None

    @property
    def price_from(self) -> str:
        """One-glance price string used on cards, e.g. `free, then $20/mo`."""
        cheapest = self.cheapest_paid
        amount = cheapest.monthly_amount if cheapest else None
        if self.model == "free":
            return "Free"
        if self.model == "open_source":
            return "Free (OSS) + your model costs" if amount is None else f"OSS · hosting from {util.format_usd(amount)}/mo"
        if amount is None:
            return "Contact sales" if self.model == "enterprise" else "Paid"
        amount_label = f"{util.format_usd(amount)}/mo"
        if self.has_free_tier and self.model == "freemium":
            return f"Free tier · from {amount_label}"
        return f"from {amount_label}"



# --------------------------------------------------------------------------- #
# Copyable examples
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class ExamplePrompt:
    """A starter prompt a reader can copy straight into the tool."""

    label: str
    text: str


@dataclass(slots=True)
class CodeExample:
    """A short snippet (shell, python, curl) with copy-to-clipboard."""

    label: str
    code: str
    language: str = "bash"


# --------------------------------------------------------------------------- #
# Tool
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class Tool:
    id: str
    name: str
    maker: str
    tagline: str
    category: str
    subcategory: str
    definition: str
    why_it_matters: str
    workplace_use_cases: list[str]
    who_uses_it: list[str]
    how_to_use: str
    key_features: list[str]
    pricing: Pricing
    official_url: str
    logo_source_note: str
    related_tools: list[str]
    launched: str
    platform: list[str]
    logo: str = ""
    featured: bool = False
    needs_verification: list[str] = field(default_factory=list)
    also_known_as: list[str] = field(default_factory=list)
    docs_url: str = ""
    example_prompts: list[ExamplePrompt] = field(default_factory=list)
    code_examples: list[CodeExample] = field(default_factory=list)
    source_file: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    # -- identity ---------------------------------------------------------- #
    @property
    def url(self) -> str:
        return util.page_url("tools", self.id)

    @property
    def monogram(self) -> str:
        return util.monogram(self.name)

    # -- pricing ----------------------------------------------------------- #
    @property
    def pricing_badge(self) -> dict[str, str]:
        return {"label": self.pricing.badge_label, "slug": self.pricing.badge_slug}

    @property
    def price_from(self) -> str:
        return self.pricing.price_from

    @property
    def verification_flag(self) -> bool:
        """True when the entry (or one of its fields) still needs a human check."""
        return bool(self.needs_verification)

    @property
    def stale_pricing(self) -> str | None:
        return util.stale_label(self.pricing.pricing_last_verified)

    # -- sorting / search -------------------------------------------------- #
    @property
    def launch_key(self) -> tuple[int, int]:
        return util.launch_sort_key(self.launched)

    def search_blob(self) -> str:
        """Lower-cased haystack for the client-side instant search."""
        parts = [self.name, *self.also_known_as, self.maker, self.tagline, self.subcategory]
        return util.collapse_ws(" ".join(parts)).lower()

    def to_index_record(self, category_name: str) -> dict[str, Any]:
        """Compact record published to `assets/data/tools.json`."""
        return {
            "id": self.id,
            "name": self.name,
            "maker": self.maker,
            "tagline": self.tagline,
            "category": self.category,
            "category_name": category_name,
            "subcategory": self.subcategory,
            "pricing_model": self.pricing.model,
            "has_free_tier": self.pricing.has_free_tier,
            "price_from": self.price_from,
            "who_uses_it": list(self.who_uses_it),
            "platform": list(self.platform),
            "launched": self.launched,
            "featured": self.featured,
            "needs_verification": list(self.needs_verification),
            "pricing_last_verified": self.pricing.pricing_last_verified,
            "official_url": self.official_url,
            "url": self.url,
        }



def _validate_pricing(
    raw: Any,
    where: str,
    problems: list[str],
    warnings: list[str],
    *,
    verified_fields: list[str],
) -> Pricing | None:
    if not isinstance(raw, dict):
        problems.append(f"{where}: `pricing` must be an object")
        return None

    pricing_waived = "pricing" in verified_fields

    model = _clean_str(raw.get("model"))
    if model not in PRICING_MODELS:
        problems.append(
            f"{where}: `pricing.model` must be one of {sorted(PRICING_MODELS)} (got {model!r})"
        )
        model = "freemium"

    has_free_tier = raw.get("has_free_tier")
    if not isinstance(has_free_tier, bool):
        problems.append(f"{where}: `pricing.has_free_tier` must be true or false")
        has_free_tier = False
    if model == "free" and not has_free_tier:
        problems.append(f"{where}: `pricing.model` is 'free' so `has_free_tier` must be true")
    if model == "paid" and has_free_tier:
        warnings.append(f"{where}: model is 'paid' but `has_free_tier` is true - is it really freemium?")

    free_details = _clean_str(raw.get("free_tier_details"))
    if not free_details:
        problems.append(
            f"{where}: `pricing.free_tier_details` is required - describe the limits, or write "
            "'No free tier - <what a paid plan costs>' when there is none"
        )
    elif not has_free_tier and not re.match(r"(?i)^(no|none|not)\b", free_details):
        warnings.append(
            f"{where}: `has_free_tier` is false but `free_tier_details` does not start with 'No'"
        )

    plans_raw = raw.get("paid_plans", [])
    if not isinstance(plans_raw, list):
        problems.append(f"{where}: `pricing.paid_plans` must be an array")
        plans_raw = []
    plans: list[PaidPlan] = []
    for index, plan in enumerate(plans_raw):
        plan_where = f"{where} pricing.paid_plans[{index}]"
        if not isinstance(plan, dict):
            problems.append(f"{plan_where}: each plan must be an object")
            continue
        name = _clean_str(plan.get("name"))
        price = _clean_str(plan.get("price"))
        if not name:
            problems.append(f"{plan_where}: `name` is required")
        if not price:
            problems.append(f"{plan_where}: `price` is required (use 'Custom / contact sales' if unpublished)")
        amount = plan.get("usd_monthly")
        if amount is not None and not isinstance(amount, (int, float)):
            problems.append(f"{plan_where}: `usd_monthly` must be a number or omitted")
            amount = None
        if price and amount is None and util.parse_monthly_usd(price) is None and "custom" not in price.lower():
            warnings.append(f"{plan_where}: cannot derive a monthly figure from price {price!r} - add `usd_monthly`")
        plans.append(PaidPlan(name=name or "?", price=price or "?", notes=_clean_str(plan.get("notes")), usd_monthly=amount))

    if model in {"paid", "freemium", "enterprise"} and not plans and not pricing_waived:
        problems.append(f"{where}: `pricing.paid_plans` needs at least one real plan for a model of {model!r}")

    verified = _clean_str(raw.get("pricing_last_verified"))
    if not verified:
        problems.append(f"{where}: `pricing.pricing_last_verified` is required (ISO date, e.g. 2026-09-22)")
    else:
        try:
            parsed = util.parse_date(verified)
            if parsed > util.parse_date(util.today_iso()):
                problems.append(f"{where}: `pricing_last_verified` ({verified}) is in the future")
        except ValueError:
            problems.append(f"{where}: `pricing_last_verified` must be YYYY-MM-DD (got {verified!r})")

    pricing_url = _clean_str(raw.get("pricing_url"))
    if pricing_url:
        _check_url(problems, where, pricing_url, "pricing.pricing_url")

    return Pricing(
        model=model,
        has_free_tier=has_free_tier,
        free_tier_details=free_details,
        paid_plans=plans,
        pricing_last_verified=verified or util.today_iso(),
        pricing_url=pricing_url,
        notes=_clean_str(raw.get("notes")),
    )


def _validate_str_list(
    problems: list[str],
    where: str,
    field_name: str,
    value: Any,
    *,
    min_items: int,
    min_len: int = 12,
    max_items: int = 12,
) -> list[str]:
    if not isinstance(value, list) or not value:
        problems.append(f"{where}: `{field_name}` must be a non-empty array of strings")
        return []
    items = [_clean_str(item) for item in value]
    if any(not item for item in items):
        problems.append(f"{where}: `{field_name}` contains an empty entry")
    items = [item for item in items if item]
    if len(items) < min_items:
        problems.append(f"{where}: `{field_name}` needs at least {min_items} entries (has {len(items)})")
    if len(items) > max_items:
        problems.append(f"{where}: `{field_name}` has {len(items)} entries - keep it to {max_items} or fewer")
    short = [item for item in items if len(item) < min_len]
    if short:
        problems.append(f"{where}: `{field_name}` entries must be at least {min_len} characters: {short[:2]!r}")
    return items


def _lint_copy(warnings: list[str], where: str, field_name: str, value: str) -> None:
    lowered = value.lower()
    for cliche in _CLICHES:
        if cliche in lowered:
            warnings.append(f"{where}: `{field_name}` uses marketing filler {cliche!r} - rewrite it")


def _validate_prompts(problems: list[str], where: str, value: Any) -> list[ExamplePrompt]:
    """Optional `example_prompts` - the copyable starter prompts on tool pages."""
    if value is None:
        return []
    if not isinstance(value, list):
        problems.append(f"{where}: `example_prompts` must be an array of {{label, text}} objects")
        return []
    if len(value) > 4:
        problems.append(f"{where}: `example_prompts` has {len(value)} entries - keep it to 4 or fewer")
    prompts: list[ExamplePrompt] = []
    for index, item in enumerate(value):
        item_where = f"{where} example_prompts[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{item_where}: must be an object with `label` and `text`")
            continue
        label = _clean_str(item.get("label"))
        text = _clean_str(item.get("text"))
        if not label:
            problems.append(f"{item_where}: `label` is required")
        if len(text) < 20:
            problems.append(f"{item_where}: `text` must be a real prompt (20+ characters)")
        if label and text:
            prompts.append(ExamplePrompt(label=label, text=text))
    return prompts


def _validate_code_examples(problems: list[str], where: str, value: Any) -> list[CodeExample]:
    """Optional `code_examples` - short snippets rendered with copy buttons."""
    if value is None:
        return []
    if not isinstance(value, list):
        problems.append(f"{where}: `code_examples` must be an array of {{label, language, code}} objects")
        return []
    if len(value) > 3:
        problems.append(f"{where}: `code_examples` has {len(value)} entries - keep it to 3 or fewer")
    examples: list[CodeExample] = []
    for index, item in enumerate(value):
        item_where = f"{where} code_examples[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{item_where}: must be an object with `label`, `language` and `code`")
            continue
        label = _clean_str(item.get("label"))
        code = _clean_str(item.get("code"))
        language = _clean_str(item.get("language")) or "bash"
        if not label:
            problems.append(f"{item_where}: `label` is required")
        if len(code) < 10:
            problems.append(f"{item_where}: `code` is too short to be useful")
        if label and code:
            examples.append(CodeExample(label=label, code=code, language=language))
    return examples


def validate_tool(
    raw: Any,
    *,
    source: str,
    categories: dict[str, Any],
    roles: dict[str, str],
    platforms: dict[str, str],
) -> tuple[Tool, list[str]]:
    """Validate one raw dict. Raises SchemaError listing every problem found.

    `categories` maps category id -> category object, `roles` maps a lower-cased
    accepted spelling -> canonical role name, `platforms` does the same for
    platforms. Unknown references are hard errors so the derived pages can
    never fall out of sync with the data.
    """
    problems: list[str] = []
    warnings: list[str] = []

    if not isinstance(raw, dict):
        raise SchemaError([f"{source}: top-level entry must be an object"])

    tool_id = _clean_str(raw.get("id"))
    where = f"{source} [{tool_id or 'missing id'}]"

    # -- identity ---------------------------------------------------------- #
    for required in ("id", "name", "maker", "tagline", "category", "subcategory"):
        if not _clean_str(raw.get(required)):
            problems.append(f"{where}: `{required}` is required")
    if tool_id and not _ID_RE.match(tool_id):
        problems.append(f"{where}: `id` must be kebab-case (a-z, 0-9, dashes)")

    name = _clean_str(raw.get("name"))
    if name and tool_id and util.slugify(name) != tool_id and tool_id not in util.slugify(name):
        warnings.append(f"{where}: `id` {tool_id!r} does not match the slug of name {name!r}")

    category = _clean_str(raw.get("category"))
    if category and category not in categories:
        problems.append(f"{where}: unknown `category` {category!r}. Valid ids: {', '.join(sorted(categories))}")

    # -- prose ------------------------------------------------------------- #
    definition = _clean_str(raw.get("definition"))
    why = _clean_str(raw.get("why_it_matters"))
    how = _clean_str(raw.get("how_to_use"))
    for field_name, value, minimum, maximum in (
        ("definition", definition, 80, 520),
        ("why_it_matters", why, 120, 900),
        ("how_to_use", how, 80, 900),
    ):
        if not value:
            problems.append(f"{where}: `{field_name}` is required")
            continue
        if len(value) < minimum:
            warnings.append(f"{where}: `{field_name}` is only {len(value)} characters - say more ({minimum}+ expected)")
        if len(value) > maximum:
            warnings.append(f"{where}: `{field_name}` is {len(value)} characters - tighten it ({maximum} max)")
        _lint_copy(warnings, where, field_name, value)

    tagline = _clean_str(raw.get("tagline"))
    if tagline and len(tagline) > 118:
        warnings.append(f"{where}: `tagline` is {len(tagline)} characters - keep cards to 118 max")

    # -- lists ------------------------------------------------------------- #
    use_cases = _validate_str_list(problems, where, "workplace_use_cases", raw.get("workplace_use_cases"), min_items=3, min_len=20, max_items=7)
    features = _validate_str_list(problems, where, "key_features", raw.get("key_features"), min_items=3, min_len=12, max_items=8)

    raw_related = raw.get("related_tools")
    if not isinstance(raw_related, list):
        problems.append(f"{where}: `related_tools` must be an array (use [] when nothing is related yet)")
        related: list[str] = []
    else:
        related = [_clean_str(item) for item in raw_related if _clean_str(item)]

    # Roles and platforms are normalised against the registries so the generated
    # "By role" pages can never drift away from the tool data.
    roles_out: list[str] = []
    raw_roles = raw.get("who_uses_it")
    if not isinstance(raw_roles, list) or not raw_roles:
        problems.append(f"{where}: `who_uses_it` must be a non-empty array")
    else:
        for entry in raw_roles:
            canonical = roles.get(_clean_str(entry).lower())
            if not canonical:
                problems.append(
                    f"{where}: unknown role {entry!r}. Add it to data/roles.json, or use one of: "
                    f"{', '.join(sorted(set(roles.values())))}"
                )
            else:
                roles_out.append(canonical)
        if len(roles_out) < 2:
            warnings.append(f"{where}: only {len(roles_out)} role(s) listed - who else really uses this at work?")

    platforms_out: list[str] = []
    raw_platforms = raw.get("platform")
    if not isinstance(raw_platforms, list) or not raw_platforms:
        problems.append(f"{where}: `platform` must be a non-empty array")
    else:
        for entry in raw_platforms:
            canonical = platforms.get(_clean_str(entry).lower())
            if not canonical:
                problems.append(
                    f"{where}: unknown platform {entry!r}. Valid values: {', '.join(sorted(set(platforms.values())))}"
                )
            else:
                platforms_out.append(canonical)

    # -- copyable examples (optional) -------------------------------------- #
    prompts = _validate_prompts(problems, where, raw.get("example_prompts"))
    code_examples = _validate_code_examples(problems, where, raw.get("code_examples"))

    # -- verification bookkeeping ------------------------------------------ #
    needs = raw.get("needs_verification", False)
    if isinstance(needs, bool):
        verified_fields = ["entry"] if needs else []
    elif isinstance(needs, list):
        verified_fields = [_clean_str(item) for item in needs if _clean_str(item)]
    else:
        problems.append(f"{where}: `needs_verification` must be true/false or an array of field names")
        verified_fields = []

    # -- pricing ----------------------------------------------------------- #
    pricing = _validate_pricing(raw.get("pricing"), where, problems, warnings, verified_fields=verified_fields)

    # -- links / provenance ------------------------------------------------ #
    official_url = _clean_str(raw.get("official_url"))
    if not official_url:
        problems.append(f"{where}: `official_url` is required")
    else:
        _check_url(problems, where, official_url, "official_url")

    logo_note = _clean_str(raw.get("logo_source_note"))
    if not logo_note:
        problems.append(
            f"{where}: `logo_source_note` is required (say where the mark comes from, or that the text fallback is used)"
        )

    launched = _clean_str(str(raw.get("launched", "")))
    if not launched:
        problems.append(f"{where}: `launched` is required (e.g. 2023 or 2023-11-30)")
    elif not _LAUNCHED_RE.match(launched):
        problems.append(f"{where}: `launched` must be YYYY, YYYY-MM or YYYY-MM-DD (got {launched!r})")

    featured = raw.get("featured", False)
    if not isinstance(featured, bool):
        problems.append(f"{where}: `featured` must be true or false")
        featured = False

    if problems:
        raise SchemaError(problems)

    if pricing is None:  # pragma: no cover - unreachable while problems are empty
        raise SchemaError([f"{where}: `pricing` could not be parsed"])

    tool = Tool(
        id=tool_id,
        name=name,
        maker=_clean_str(raw.get("maker")),
        tagline=tagline,
        category=category,
        subcategory=_clean_str(raw.get("subcategory")),
        definition=definition,
        why_it_matters=why,
        workplace_use_cases=use_cases,
        who_uses_it=roles_out,
        how_to_use=how,
        key_features=features,
        pricing=pricing,
        official_url=official_url,
        logo_source_note=logo_note,
        related_tools=related,
        launched=launched,
        platform=platforms_out,
        logo=_clean_str(raw.get("logo")),
        featured=featured,
        needs_verification=verified_fields,
        also_known_as=[_clean_str(a) for a in raw.get("also_known_as", []) if _clean_str(a)],
        docs_url=_clean_str(raw.get("docs_url")),
        example_prompts=prompts,
        code_examples=code_examples,
        source_file=source,
        raw=raw,
    )
    return tool, warnings





# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def _clean_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _check_url(problems: list[str], where: str, value: str, field_name: str) -> None:
    if not _URL_RE.match(value):
        problems.append(f"{where}: `{field_name}` must be an absolute https URL (got {value!r})")
    elif any(token in value.lower() for token in ("example.com", "localhost", "bit.ly", "utm_")):
        problems.append(f"{where}: `{field_name}` looks like a placeholder or tracking URL ({value!r})")
