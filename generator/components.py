"""Reusable HTML fragments.

Every function here returns a string of escaped HTML. Nothing in this module
reads files or knows about URLs on disk: it receives a `Context` (site config,
registry, link rewriter) and data objects. That is what keeps the data layer
swappable and the templates testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from . import data as data_module
from . import icons, schema, util


@dataclass(slots=True)
class Context:
    """Everything a fragment needs to render."""

    site: dict[str, Any]
    registry: data_module.Registry
    depth: int = 0

    def __post_init__(self) -> None:
        self.link = util.Linker(self.depth)

    link: util.Linker = None  # type: ignore[assignment]

    @property
    def base_url(self) -> str:
        return str(self.site.get("url", "")).rstrip("/")

    def absolute(self, path: str) -> str:
        return self.base_url + path

    def role_slug(self, name: str) -> str:
        role = self.registry.roles_by_name.get(name)
        return role.slug if role else util.slugify(name)

    def platform_slug(self, name: str) -> str:
        for platform in self.registry.platforms:
            if platform.name == name:
                return platform.slug
        return util.slugify(name)


# --------------------------------------------------------------------------- #
# Small pieces
# --------------------------------------------------------------------------- #
def search_form(ctx: Context, *, value: str = "", action: str, placeholder: str, extra_class: str = "") -> str:
    """Search box. Submits as a plain GET so it works without JavaScript."""
    return f"""<form class="search-form {extra_class}" role="search" action="{util.esc(ctx.link(action))}" method="get">
      {icons.icon('search', size=18)}
      <input type="search" name="q" value="{util.esc(value)}" placeholder="{util.esc(placeholder)}"
             aria-label="Search tools" autocomplete="off" spellcheck="false" data-search>
    </form>"""


def pricing_badge(pricing: schema.Pricing) -> str:
    return (
        f'<span class="badge badge--pricing badge--{util.esc(pricing.badge_slug)}">'
        f"{util.esc(pricing.badge_label)}</span>"
    )


def category_badge(ctx: Context, category: data_module.Category) -> str:
    return (
        f'<a class="badge badge--cat" href="{util.esc(ctx.link(category.url))}" '
        f'style="--cat: {util.esc(category.accent)};">{util.esc(category.short_name)}</a>'
    )


def logo_mark(ctx: Context, tool: schema.Tool, *, large: bool = False) -> str:
    """Tool mark: official asset when one has been committed, monogram otherwise."""
    css = "tool-logo tool-logo--lg" if large else "tool-logo"
    if tool.logo:
        return (
            f'<span class="{css}"><img src="{util.esc(ctx.link("/assets/logos/" + tool.logo))}" '
            f'alt="" width="36" height="36" loading="lazy" decoding="async"></span>'
        )
    return f'<span class="{css}" aria-hidden="true">{util.esc(tool.monogram)}</span>'


def stats_strip(items: Sequence[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div class="stats__item"><span class="stats__value">{util.esc(value)}</span>'
        f'<span class="stats__label">{util.esc(label)}</span></div>'
        for value, label in items
    )
    return f'<div class="stats">{cells}</div>'


def callout(text: str, *, kind: str = "info", icon: str | None = None) -> str:
    icon_name = icon or ("alert" if kind == "warn" else "check" if kind == "ok" else "spark")
    modifier = f" callout--{kind}" if kind in {"warn", "ok"} else ""
    return (
        f'<div class="callout{modifier}">{icons.icon(icon_name, size=18)}'
        f'<p class="callout__body">{text}</p></div>'
    )


def section_head(title: str, sub: str = "", action: str = "") -> str:
    sub_html = f"<p>{sub}</p>" if sub else ""
    action_html = f'<div class="section__head__action">{action}</div>' if action else ""
    return (
        f'<div class="section__head"><div><h2>{title}</h2>{sub_html}</div>{action_html}</div>'
    )


def breadcrumbs(ctx: Context, items: Sequence[tuple[str, str]]) -> str:
    """`[("Directory", "/directory/"), ("ChatGPT", "")]` (last item = current page)."""
    parts = []
    last_index = len(items) - 1
    for index, (label, href) in enumerate(items):
        if href and index != last_index:
            parts.append(f'<li><a href="{util.esc(ctx.link(href))}">{util.esc(label)}</a></li>')
        else:
            parts.append(f'<li aria-current="page">{util.esc(label)}</li>')
    return '<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>' + "".join(parts) + "</ol></nav>"


def code_block(block_id: str, label: str, code: str) -> str:
    """Copyable snippet. The copy button is wired up by site.js."""
    return f"""<figure class="code-block">
      <figcaption class="code-block__head">
        <span class="code-block__label">{util.esc(label)}</span>
        <button type="button" class="copy-button" data-copy-target="{util.esc(block_id)}" aria-label="Copy {util.esc(label)}">
          {icons.icon('copy', size=13)}<span data-copy-label>Copy</span>
        </button>
      </figcaption>
      <pre><code id="{util.esc(block_id)}">{util.esc(code)}</code></pre>
    </figure>"""


# --------------------------------------------------------------------------- #
# Cards
# --------------------------------------------------------------------------- #
def code_block_html(block_id: str, label: str, highlighted: str) -> str:
    """Copyable snippet where the body is already-highlighted HTML."""
    return f"""<figure class="code-block">
      <figcaption class="code-block__head">
        <span class="code-block__label">{util.esc(label)}</span>
        <button type="button" class="copy-button" data-copy-target="{util.esc(block_id)}" aria-label="Copy {util.esc(label)}">
          {icons.icon('copy', size=13)}<span data-copy-label>Copy</span>
        </button>
      </figcaption>
      <pre><code id="{util.esc(block_id)}">{highlighted}</code></pre>
    </figure>"""


def _card_data_attrs(ctx: Context, tool: schema.Tool, category: data_module.Category) -> str:
    """Filtering hooks. Everything filters.js needs is on the card already."""
    roles = "|".join(ctx.role_slug(role) for role in tool.who_uses_it)
    platforms = "|".join(ctx.platform_slug(platform) for platform in tool.platform)
    keywords = " ".join(
        [
            tool.name,
            *tool.also_known_as,
            tool.maker,
            tool.subcategory.replace("-", " "),
            category.name,
            category.short_name,
            *tool.who_uses_it,
            *tool.platform,
            " ".join(tool.key_features),
        ]
    ).lower()
    launched = "".join(part.zfill(2) for part in tool.launched.split("-")) if tool.launched else ""
    return (
        f'data-tool data-name="{util.esc(tool.name.lower())}" data-maker="{util.esc(tool.maker.lower())}" '
        f'data-search="{util.esc(tool.search_blob())}" data-keywords="{util.esc(keywords)}" '
        f'data-category="{util.esc(category.id)}" data-pricing="{util.esc(tool.pricing.model)}" '
        f'data-roles="{util.esc(roles)}" data-platforms="{util.esc(platforms)}" '
        f'data-launched="{util.esc(launched)}" data-featured="{"true" if tool.featured else "false"}"'
    )


def tool_card(ctx: Context, tool: schema.Tool) -> str:
    category = ctx.registry.category_of(tool)
    flags = ""
    if tool.verification_flag:
        flags = (
            f'<span class="badge badge--flag" title="This entry still needs a human verification pass">'
            f"Needs verification</span>"
        )
    price_class = "tool-card__price tool-card__price--free" if tool.pricing.has_free_tier else "tool-card__price"
    return f"""<article class="tool-card" style="--cat: {util.esc(category.accent)};" {_card_data_attrs(ctx, tool, category)}>
      <div class="tool-card__head">
        {logo_mark(ctx, tool)}
        <div class="tool-card__titles">
          <h3 class="tool-card__name"><a href="{util.esc(ctx.link(tool.url))}">{util.esc(tool.name)}</a></h3>
          <span class="tool-card__maker">{util.esc(tool.maker)}</span>
        </div>
        <div class="tool-card__badges">{pricing_badge(tool.pricing)}</div>
      </div>
      <p class="tool-card__tagline">{util.esc(tool.tagline)}</p>
      <div class="tool-card__meta">
        <span class="{price_class}">{util.esc(tool.price_from)}</span>
        {flags}
        {category_badge(ctx, category)}
      </div>
    </article>"""


def category_card(ctx: Context, category: data_module.Category) -> str:
    count = f"{category.count} tool{'s' if category.count != 1 else ''}"
    return f"""<a class="category-card" href="{util.esc(ctx.link(category.url))}" style="--cat: {util.esc(category.accent)};">
      <span class="category-card__top">
        {icons.icon(category.icon, size=22)}
        <span class="category-card__count">{util.esc(count)}</span>
      </span>
      <span class="category-card__name">{util.esc(category.short_name)}</span>
      <p class="category-card__desc">{util.esc(category.description)}</p>
    </a>"""


def role_card(ctx: Context, role: data_module.Role) -> str:
    return f"""<a class="category-card" href="{util.esc(ctx.link(role.url))}" style="--cat: hsl(330 60% 70%);">
      <span class="category-card__top">
        {icons.icon('users', size=22)}
        <span class="category-card__count">{role.count} tool{'s' if role.count != 1 else ''}</span>
      </span>
      <span class="category-card__name">{util.esc(role.name)}</span>
      <p class="category-card__desc">{util.esc(role.blurb)}</p>
    </a>"""


# --------------------------------------------------------------------------- #
# Directory: filters and toolbar
# --------------------------------------------------------------------------- #
def filter_option(group: str, value: str, label: str, count: int, *, checked: bool = False, locked: bool = False) -> str:
    return f"""<label class="filter-option">
          <input type="checkbox" data-filter-input="{util.esc(group)}" value="{util.esc(value)}"
                 data-label="{util.esc(label)}"{' checked' if checked else ''}{' data-locked' if locked else ''}>
          <span class="filter-option__label">{util.esc(label)}</span>
          <span class="filter-option__count" data-count-for="{util.esc(value)}">{count}</span>
        </label>"""


def filter_panel(groups: Sequence[tuple[str, str, list[tuple[str, str, int]], Sequence[str]]]) -> str:
    """`groups` = list of (group key, legend, [(value, label, count)], locked values)."""
    blocks = []
    for key, legend, options, locked in groups:
        if not options:
            continue
        opts = "".join(
            filter_option(key, value, label, count, locked=value in locked) for value, label, count in options
        )
        blocks.append(
            f'<fieldset class="filter-group"><legend>{util.esc(legend)}</legend>'
            f'<div class="filter-group__options">{opts}</div></fieldset>'
        )
    return f"""<aside class="filters" aria-labelledby="filters-title">
      <div class="filters__head">
        <span class="filters__title" id="filters-title">{icons.icon('filter', size=15)} Filters</span>
        <button type="button" class="button button--ghost button--sm" data-clear>Clear all</button>
      </div>
      {"".join(blocks)}
    </aside>"""


def results_toolbar(ctx: Context, *, action: str, total: int, placeholder: str = "Filter these tools…") -> str:
    return f"""<div class="results-toolbar">
      {search_form(ctx, action=action, placeholder=placeholder)}
      <p class="results-count" data-results-count aria-live="polite"><strong>{total}</strong> of {total} tools</p>
      <label class="sort-field">Sort
        <select data-sort>
          <option value="relevant">Most relevant</option>
          <option value="az">A–Z</option>
          <option value="newest">Newest first</option>
        </select>
      </label>
    </div>
    <ul class="active-filters" data-active-filters aria-label="Active filters"></ul>"""


def empty_state(message: str = "No tools match these filters yet.") -> str:
    return f"""<div class="empty-state" data-empty hidden>
      {icons.icon('search', size=26)}
      <h3>Nothing matches yet</h3>
      <p>{util.esc(message)}</p>
      <p class="small muted">Loosen a filter, or clear the search and try a broader term.</p>
    </div>"""


# --------------------------------------------------------------------------- #
# Tool detail pieces
# --------------------------------------------------------------------------- #
def _host(url: str) -> str:
    return url.split("//", 1)[-1].split("/", 1)[0].removeprefix("www.")


def fact_list(ctx: Context, tool: schema.Tool) -> str:
    category = ctx.registry.category_of(tool)
    rows: list[tuple[str, str]] = [
        ("Maker", util.esc(tool.maker)),
        ("Category", f'<a href="{util.esc(ctx.link(category.url))}">{util.esc(category.short_name)}</a>'),
        ("Launched", util.esc(tool.launched)),
        ("Platforms", util.esc(", ".join(tool.platform))),
        ("Pricing model", util.esc(tool.pricing.badge_label)),
        ("Free tier", "Yes" if tool.pricing.has_free_tier else "No"),
        (
            "Price checked",
            f'<time datetime="{util.esc(tool.pricing.pricing_last_verified)}">'
            f"{util.esc(tool.pricing.pricing_last_verified)}</time>",
        ),
        (
            "Official site",
            f'<a href="{util.esc(tool.official_url)}" target="_blank" rel="noopener noreferrer nofollow">'
            f"{util.esc(_host(tool.official_url))} {icons.icon('external', size=13)}</a>",
        ),
    ]
    if tool.docs_url:
        rows.append(
            ("Docs", f'<a href="{util.esc(tool.docs_url)}" target="_blank" rel="noopener noreferrer nofollow">'
                     f"{util.esc(_host(tool.docs_url))}</a>")
        )
    body = "".join(f'<div class="fact-list__row"><dt>{label}</dt><dd>{value}</dd></div>' for label, value in rows)
    return f'<dl class="fact-list">{body}</dl>'


def pricing_table(tool: schema.Tool) -> str:
    pricing = tool.pricing
    rows = []
    free_price = "$0" if pricing.has_free_tier else "—"
    rows.append(
        f'<tr><td class="plan-name">Free</td><td class="plan-price">{free_price}</td>'
        f'<td class="plan-notes">{util.esc(pricing.free_tier_details)}</td></tr>'
    )
    for plan in pricing.paid_plans:
        rows.append(
            f'<tr><td class="plan-name">{util.esc(plan.name)}</td>'
            f'<td class="plan-price">{util.esc(plan.price)}</td>'
            f'<td class="plan-notes">{util.esc(plan.notes)}</td></tr>'
        )
    return f"""<div class="table-scroll">
      <table class="pricing-table">
        <caption>Verified {util.esc(pricing.pricing_last_verified)} — confirm current pricing on the vendor's own page.</caption>
        <thead><tr><th scope="col">Plan</th><th scope="col">Price</th><th scope="col">What you get</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>"""


def related_tools(ctx: Context, tools: Sequence[schema.Tool]) -> str:
    if not tools:
        return '<p class="small muted">No cross-links recorded yet.</p>'
    items = "".join(
        f'<li><a href="{util.esc(ctx.link(tool.url))}">{util.esc(tool.name)}'
        f"<span>{util.esc(tool.pricing.badge_label)}</span></a></li>"
        for tool in tools
    )
    return f'<ul class="related-list">{items}</ul>'


def role_links(ctx: Context, names: Sequence[str]) -> str:
    items = "".join(
        f'<li><a class="badge badge--soft" href="{util.esc(ctx.link(util.page_url("roles", ctx.role_slug(name))))}">'
        f"{util.esc(name)}</a></li>"
        for name in names
    )
    return f'<ul class="tag-list">{items}</ul>'

