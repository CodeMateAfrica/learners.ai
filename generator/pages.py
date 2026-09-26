from __future__ import annotations

from typing import Iterable, Sequence

from . import components, data, schema, templates, util


def _depth_for(path: str) -> int:
    cleaned = path.strip("/")
    if not cleaned:
        return 0
    return max(1, len(cleaned.split("/")))


def _page_ctx(registry: data.Registry, path: str) -> components.Context:
    return components.Context(site=registry.site, registry=registry, depth=_depth_for(path))


def _page_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def home_page(registry: data.Registry) -> str:
    ctx = _page_ctx(registry, "/")
    hero = registry.site.get("hero", {})
    featured = "".join(components.tool_card(ctx, tool) for tool in registry.featured[:6])
    categories = "".join(components.category_card(ctx, category) for category in registry.categories)
    stats = components.stats_strip(
        [
            (f"{len(registry.tools)}", "tools"),
            (f"{len(registry.categories)}", "categories"),
            (f"{len(registry.roles)}", "roles"),
            (f"{registry.free_tier_share}%", "free-tier share"),
        ]
    )
    body = f"""
    <section class="hero wrap">
      <div class="hero__content">
        <p class="eyebrow">{util.esc(hero.get('eyebrow','Open reference'))}</p>
        <h1>{util.esc(hero.get('headline','Every AI tool. What it is, who it is for, what it costs.'))}</h1>
        <p class="lede">{util.esc(hero.get('sub','A curated list of AI tools for professional work.'))}</p>
        {components.search_form(ctx, action="/directory/", placeholder="Search tools by name, category, or use case", extra_class="hero-search")}
      </div>
      {stats}
    </section>

    <section class="wrap section">
      {components.section_head('Featured tools', 'A quick shortlist of the most relevant entries for daily work.')}
      <div class="grid grid--cards">{featured}</div>
    </section>

    <section class="wrap section">
      {components.section_head('Browse by category', 'Twenty categories, each with its own navigable index.')}
      <div class="grid grid--categories">{categories}</div>
    </section>
    """
    return templates.render_page(
        ctx,
        title=f"{registry.site.get('name', 'learners.ai')} — AI tooling reference",
        description=registry.site.get('description', ''),
        path="/",
        body=body,
        active="/",
    )


def category_page(registry: data.Registry, category: data.Category) -> str:
    ctx = _page_ctx(registry, category.url)
    tools = sorted(category.tools, key=lambda tool: (tool.name.lower(), tool.maker.lower()))
    body = _directory_body(registry, ctx, tools, locked_category=category)
    return templates.render_page(
        ctx,
        title=f"{category.name} — learners.ai",
        description=category.description,
        path=category.url,
        body=body,
        active="/categories/",
    )


def directory_page(registry: data.Registry) -> str:
    ctx = _page_ctx(registry, "/directory/")
    tools = sorted(registry.tools, key=lambda tool: tool.name.lower())
    body = _directory_body(registry, ctx, tools, locked_category=None, title="Global directory")
    return templates.render_page(
        ctx,
        title="Directory — learners.ai",
        description="Search every AI tool in the learners.ai catalogue.",
        path="/directory/",
        body=body,
        active="/directory/",
    )


def role_page(registry: data.Registry, role: data.Role) -> str:
    ctx = _page_ctx(registry, role.url)
    tools = sorted(role.tools, key=lambda tool: tool.name.lower())
    body = _directory_body(registry, ctx, tools, title=f"AI tools for {role.name}", locked_category=None, role_filter=role)
    return templates.render_page(
        ctx,
        title=f"AI tools for {role.name} — learners.ai",
        description=role.blurb,
        path=role.url,
        body=body,
        active="/roles/",
    )


def all_categories_page(registry: data.Registry) -> str:
    ctx = _page_ctx(registry, "/categories/")
    cards = "".join(components.category_card(ctx, category) for category in registry.categories)
    body = f"""
    <section class="wrap section">
      {components.section_head('All categories', 'Every top-level taxonomy in the reference.')}
      <div class="grid grid--categories">{cards}</div>
    </section>
    """
    return templates.render_page(
        ctx,
        title="Categories — learners.ai",
        description="Browse each AI tool category in the learners.ai directory.",
        path="/categories/",
        body=body,
        active="/categories/",
    )


def roles_page(registry: data.Registry) -> str:
    ctx = _page_ctx(registry, "/roles/")
    cards = "".join(components.role_card(ctx, role) for role in sorted(registry.roles, key=lambda role: role.name))
    body = f"""
    <section class="wrap section">
      {components.section_head('Browse by role', 'See which tools match each professional audience.')}
      <div class="grid grid--roles">{cards}</div>
    </section>
    """
    return templates.render_page(
        ctx,
        title="By role — learners.ai",
        description="Search AI tools by the audiences they are designed for.",
        path="/roles/",
        body=body,
        active="/roles/",
    )


def about_page(registry: data.Registry) -> str:
    ctx = _page_ctx(registry, "/about/")
    body = f"""
    <section class="wrap section narrow">
      {components.section_head('Method & sources', 'A simple, practical process for keeping the directory useful and honest.')}
      <div class="prose">
        <p>learners.ai is designed as a hand-curated reference for working professionals. We prioritize a small number of well-explained tools over a sprawling but unreliable list.</p>
        <p>Every tool entry records a real date for when pricing was checked, and each page tells readers to confirm the latest plan on the vendor's own site before spending budget.</p>
        <p>Contributions are welcome through GitHub issues or pull requests. If a pricing tier, URL, or category description changes, update the JSON entry and run the generator again.</p>
      </div>
    </section>
    """
    return templates.render_page(
        ctx,
        title="Method & sources — learners.ai",
        description="How learners.ai selects tools, verifies prices, and keeps the directory maintainable.",
        path="/about/",
        body=body,
        active="/about/",
    )


def tool_page(registry: data.Registry, tool: schema.Tool) -> str:
    ctx = _page_ctx(registry, tool.url)
    category = registry.category_of(tool)
    related = registry.related(tool)
    flags = ""
    if tool.verification_flag:
        flags = (
            f'<span class="badge badge--flag" title="This entry still needs a human verification pass">'
            f"Needs verification</span>"
        )
    body = f"""
    <div class="wrap">
      {components.breadcrumbs(ctx, [("Directory", "/directory/"), (category.short_name, category.url), (tool.name, "")])}
    </div>

    <section class="wrap tool-header" style="--cat: {util.esc(category.accent)};">
      <div class="tool-header__identity">
        <div class="tool-header__row">
          {components.logo_mark(ctx, tool, large=True)}
          <div>
            <p class="eyebrow" style="margin-bottom:0.2rem;">{util.esc(category.short_name)}</p>
            <h1>{util.esc(tool.name)}</h1>
            <p class="tool-header__maker">by {util.esc(tool.maker)}</p>
          </div>
        </div>
        <p class="tool-tagline">{util.esc(tool.tagline)}</p>
        <div class="tool-header__badges">
          {components.pricing_badge(tool.pricing)}
          {components.category_badge(ctx, category)}
          {flags}
        </div>
      </div>
      <div>
        {components.fact_list(ctx, tool)}
      </div>
    </section>

    <section class="wrap tool-body" style="--cat: {util.esc(category.accent)};">
      <article class="prose">
        <h2>What it is</h2>
        <p>{util.esc(tool.definition)}</p>

        <h2>Why it matters</h2>
        <p>{util.esc(tool.why_it_matters)}</p>

        <h2>Workplace use cases</h2>
        <ul>{''.join(f'<li>{util.esc(item)}</li>' for item in tool.workplace_use_cases)}</ul>

        <h2>Who uses it</h2>
        {components.role_links(ctx, tool.who_uses_it)}

        <h2>How to use it</h2>
        <p>{util.esc(tool.how_to_use)}</p>

        <h2>Key features</h2>
        <ul>{''.join(f'<li>{util.esc(item)}</li>' for item in tool.key_features)}</ul>
      </article>

      <aside class="side-panel">
        <div class="side-card">
          <h2>Pricing Details</h2>
          {components.pricing_table(tool)}
        </div>
        <div class="side-card">
          <h2>Related tools</h2>
          {components.related_tools(ctx, related)}
        </div>
      </aside>
    </section>
    """
    return templates.render_page(
        ctx,
        title=f"{tool.name} — learners.ai",
        description=tool.tagline,
        path=tool.url,
        body=body,
        active="/directory/",
    )


def _directory_body(
    registry: data.Registry,
    ctx: components.Context,
    tools: Sequence[schema.Tool],
    *,
    title: str = "Directory",
    locked_category: data.Category | None = None,
    role_filter: data.Role | None = None,
) -> str:
    category_options = []
    for category in registry.categories:
        if category.count > 0:
            category_options.append((category.id, category.short_name, len(category.tools)))

    pricing_counts = {model: 0 for model in schema.PRICING_MODELS}
    for tool in registry.tools:
        pricing_counts[tool.pricing.model] += 1
    pricing_options = [(model, info["label"], pricing_counts.get(model, 0)) for model, info in schema.PRICING_MODELS.items()]

    role_options = []
    for role in registry.roles:
        if role.count > 0:
            role_options.append((ctx.role_slug(role.name), role.name, role.count))

    platform_counts: dict[str, int] = {}
    for tool in registry.tools:
        for platform in tool.platform:
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
    platform_options = []
    for platform in registry.platforms:
        if platform.count > 0:
            platform_options.append((ctx.platform_slug(platform.name), platform.name, platform.count))

    locked = [locked_category.id] if locked_category else []
    filters = components.filter_panel(
        [
            ("category", "Category", category_options, locked),
            ("pricing", "Pricing", pricing_options, []),
            ("role", "Role", role_options, [ctx.role_slug(role_filter.name)] if role_filter else []),
            ("platform", "Platform", platform_options, []),
        ]
    )
    cards = "".join(components.tool_card(ctx, tool) for tool in tools)
    body = f"""
    <section class="wrap section">
      <div class="directory" data-directory>
        {filters}
        <div class="results-panel">
          {components.section_head(title, 'Filter by pricing, role, platform, or search for a tool by name and use case.')}
          {components.results_toolbar(ctx, action="/directory/", total=len(tools), placeholder="Search tools…")}
          <div class="grid grid--cards" data-results>
            {cards}
            {components.empty_state()}
          </div>
        </div>
      </div>
    </section>
    """
    return body
