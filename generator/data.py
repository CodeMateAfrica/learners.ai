"""Loads `data/*.json` and builds every index the site generator needs.

This module is the only place that knows about files on disk. Renderers receive
a `Registry` and never touch the filesystem, which keeps the data layer and the
templating layer cleanly separated (the brief's most important architectural
rule).
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any

from . import schema, util

#: Hand-picked hue per category family so the directory reads as designed
#: rather than as a hash of colours. Kept in the data file; documented here.
DEFAULT_HUE = 320


@dataclass(slots=True)
class Category:
    id: str
    name: str
    short_name: str
    description: str
    icon: str
    hue: int
    order: int
    tools: list[schema.Tool] = field(default_factory=list)

    @property
    def url(self) -> str:
        return util.page_url("categories", self.id)

    @property
    def count(self) -> int:
        return len(self.tools)

    @property
    def accent(self) -> str:
        return f"hsl({self.hue} 78% 68%)"

    @property
    def accent_soft(self) -> str:
        return f"hsl({self.hue} 78% 68% / 0.14)"

    @property
    def badge_slugs(self) -> list[str]:
        seen: list[str] = []
        for tool in self.tools:
            if tool.pricing.badge_slug not in seen:
                seen.append(tool.pricing.badge_slug)
        return seen

    @property
    def launch_years(self) -> list[str]:
        return sorted({str(t.launched)[:4] for t in self.tools}, reverse=True)


@dataclass(slots=True)
class Role:
    id: str
    name: str
    slug: str
    blurb: str
    aliases: list[str] = field(default_factory=list)
    tools: list[schema.Tool] = field(default_factory=list)

    @property
    def url(self) -> str:
        return util.page_url("roles", self.slug)

    @property
    def count(self) -> int:
        return len(self.tools)


@dataclass(slots=True)
class Platform:
    name: str
    slug: str
    aliases: list[str] = field(default_factory=list)
    tools: list[schema.Tool] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.tools)


@dataclass(slots=True)
class Registry:
    site: dict[str, Any]
    categories: list[Category]
    roles: list[Role]
    platforms: list[Platform]
    tools: list[schema.Tool]
    warnings: list[str] = field(default_factory=list)

    # -- lookups ----------------------------------------------------------- #
    @property
    def categories_by_id(self) -> dict[str, Category]:
        return {c.id: c for c in self.categories}

    @property
    def roles_by_name(self) -> dict[str, Role]:
        return {r.name: r for r in self.roles}

    @property
    def roles_by_slug(self) -> dict[str, Role]:
        return {r.slug: r for r in self.roles}

    @property
    def tools_by_id(self) -> dict[str, schema.Tool]:
        return {t.id: t for t in self.tools}

    @property
    def platforms_by_slug(self) -> dict[str, Platform]:
        return {p.slug: p for p in self.platforms}

    def category_of(self, tool: schema.Tool) -> Category:
        return self.categories_by_id[tool.category]

    def related(self, tool: schema.Tool) -> list[schema.Tool]:
        by_id = self.tools_by_id
        return [by_id[rid] for rid in tool.related_tools if rid in by_id]

    # -- stats ------------------------------------------------------------- #
    @property
    def populated_categories(self) -> list[Category]:
        return [c for c in self.categories if c.tools]

    @property
    def empty_categories(self) -> list[Category]:
        return [c for c in self.categories if not c.tools]

    @property
    def featured(self) -> list[schema.Tool]:
        flagged = [t for t in self.tools if t.featured]
        return flagged or self.newest(limit=8)

    @property
    def pricing_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {model: 0 for model in schema.PRICING_MODELS}
        for tool in self.tools:
            counts[tool.pricing.model] += 1
        return counts

    @property
    def free_tier_share(self) -> int:
        if not self.tools:
            return 0
        return round(100 * sum(1 for t in self.tools if t.pricing.has_free_tier) / len(self.tools))

    @property
    def last_verified(self) -> str:
        dates = [t.pricing.pricing_last_verified for t in self.tools if t.pricing.pricing_last_verified]
        return max(dates) if dates else util.today_iso()

    @property
    def unverified_count(self) -> int:
        return sum(1 for t in self.tools if t.verification_flag)

    def newest(self, limit: int = 8) -> list[schema.Tool]:
        return sorted(self.tools, key=lambda t: (t.launch_key, t.name), reverse=True)[:limit]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _category_from(raw: dict[str, Any], index: int) -> Category:
    return Category(
        id=raw["id"],
        name=raw["name"],
        short_name=util.collapse_ws(raw.get("short_name") or raw["name"]),
        description=util.collapse_ws(raw.get("description", "")),
        icon=raw.get("icon", "dot"),
        hue=int(raw.get("hue", DEFAULT_HUE)),
        order=int(raw.get("order", index)),
    )


def _load_site(root: pathlib.Path) -> dict[str, Any]:
    path = root / "data" / "site.json"
    if not path.exists():
        raise schema.SchemaError([f"missing {path.relative_to(root)}"])
    site = util.read_json(path)
    if not isinstance(site, dict):
        raise schema.SchemaError(["data/site.json must contain an object"])
    return site


def _load_registry_file(root: pathlib.Path, relative: str, key: str) -> list[dict[str, Any]]:
    path = root / relative
    if not path.exists():
        raise schema.SchemaError([f"missing {relative}"])
    payload = util.read_json(path)
    entries = payload.get(key) if isinstance(payload, dict) else payload
    if not isinstance(entries, list) or not entries:
        raise schema.SchemaError([f"{relative} must contain a non-empty `{key}` array"])
    return [entry for entry in entries if isinstance(entry, dict)]


def load(root: pathlib.Path, *, strict: bool = False, only: list[str] | None = None) -> Registry:
    """Read every data file, validate, cross-check and return a `Registry`.

    `only` restricts the load to specific category ids (used by tests and by
    `--only` builds while the data set is still being filled in).
    """
    root = pathlib.Path(root)
    problems: list[str] = []
    warnings: list[str] = []

    site = _load_site(root)
    categories = sorted(
        (
            _category_from(raw, index)
            for index, raw in enumerate(_load_registry_file(root, "data/categories.json", "categories"))
        ),
        key=lambda c: (c.order, c.name),
    )
    category_ids = [c.id for c in categories]
    if len(set(category_ids)) != len(category_ids):
        problems.append("data/categories.json: duplicate category ids")
    for category_id in category_ids:
        if not schema._ID_RE.match(category_id):
            problems.append(f"data/categories.json: id {category_id!r} must be snake_case")
    categories_by_id = {c.id: c for c in categories}

    roles: list[Role] = []
    role_lookup: dict[str, str] = {}
    for entry in _load_registry_file(root, "data/roles.json", "roles"):
        role = Role(
            id=entry.get("id", util.slugify(entry.get("name", ""))),
            name=entry["name"],
            slug=util.slugify(entry.get("slug") or entry["name"]),
            blurb=util.collapse_ws(entry.get("blurb", "")),
            aliases=[a for a in entry.get("aliases", []) if isinstance(a, str)],
        )
        roles.append(role)
        for spelling in [role.name, *role.aliases]:
            key = util.collapse_ws(spelling).lower()
            if key in role_lookup and role_lookup[key] != role.name:
                problems.append(f"data/roles.json: alias {spelling!r} is claimed by two roles")
            role_lookup[key] = role.name

    platforms: list[Platform] = []
    platform_lookup: dict[str, str] = {}
    for entry in _load_registry_file(root, "data/platforms.json", "platforms"):
        platform = Platform(
            name=entry["name"],
            slug=util.slugify(entry.get("slug") or entry["name"]),
            aliases=[a for a in entry.get("aliases", []) if isinstance(a, str)],
        )
        platforms.append(platform)
        for spelling in [platform.name, *platform.aliases]:
            platform_lookup[util.collapse_ws(spelling).lower()] = platform.name

    # -- tools ------------------------------------------------------------- #
    tools_dir = root / "data" / "tools"
    files = sorted(tools_dir.glob("*.json"))
    if not files:
        raise schema.SchemaError([f"no tool files found in {tools_dir.relative_to(root)}"])

    tools: list[schema.Tool] = []
    for path in files:
        expected = path.stem
        if expected not in categories_by_id:
            problems.append(f"data/tools/{path.name}: filename must match a category id ({expected!r} is not one)")
        payload = util.read_json(path)
        if not isinstance(payload, list):
            problems.append(f"data/tools/{path.name}: top level must be an array of tool objects")
            continue
        for raw in payload:
            if only and isinstance(raw, dict) and raw.get("category") not in only:
                continue
            try:
                tool, tool_warnings = schema.validate_tool(
                    raw,
                    source=f"data/tools/{path.name}",
                    categories=categories_by_id,
                    roles=role_lookup,
                    platforms=platform_lookup,
                )
            except schema.SchemaError as exc:
                problems.extend(exc.problems)
                continue
            if tool.category != expected:
                problems.append(
                    f"data/tools/{path.name} [{tool.id}]: category {tool.category!r} must live in "
                    f"data/tools/{tool.category}.json"
                )
            warnings.extend(tool_warnings)
            tools.append(tool)

    # -- cross-checks ------------------------------------------------------ #
    seen: dict[str, str] = {}
    for tool in tools:
        if tool.id in seen:
            problems.append(f"duplicate tool id {tool.id!r} in {tool.source_file} and {seen[tool.id]}")
        seen[tool.id] = tool.source_file
    by_id = {t.id: t for t in tools}
    for tool in tools:
        for related_id in tool.related_tools:
            if related_id == tool.id:
                problems.append(f"[{tool.id}]: `related_tools` cannot reference itself")
            elif related_id not in by_id:
                problems.append(f"[{tool.id}]: `related_tools` references unknown tool id {related_id!r}")
        if tool.logo and not (root / "assets" / "logos" / tool.logo).exists():
            problems.append(f"[{tool.id}]: logo file assets/logos/{tool.logo} does not exist")

    # -- ordering / assignment -------------------------------------------- #
    tools.sort(key=lambda t: t.name.lower())
    for tool in tools:
        categories_by_id[tool.category].tools.append(tool)
        for role_name in tool.who_uses_it:
            next(r for r in roles if r.name == role_name).tools.append(tool)
        for platform_name in tool.platform:
            next(p for p in platforms if p.name == platform_name).tools.append(tool)

    for category in categories:
        if not category.tools:
            warnings.append(f"category {category.id!r} has no tools yet - it renders as an empty page")
    for role in roles:
        if not role.tools:
            warnings.append(f"role {role.name!r} is not used by any tool yet")
    for tool in tools:
        if tool.stale_pricing:
            warnings.append(f"[{tool.id}]: pricing {tool.stale_pricing} - re-verify against {tool.official_url}")

    if problems:
        raise schema.SchemaError(problems)
    if strict and warnings:
        raise schema.SchemaError([f"(strict) {w}" for w in warnings])

    return Registry(
        site=site,
        categories=categories,
        roles=roles,
        platforms=platforms,
        tools=tools,
        warnings=warnings,
    )



