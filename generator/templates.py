"""The page shell: `<head>`, site header, site footer.

Templates are plain f-strings with named slots - no template engine, no
dependencies. Page-specific markup is composed in `pages.py` and passed in as
`body`.
"""

from __future__ import annotations

from typing import Sequence

from . import components, icons, util

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<link rel="icon" href="{favicon}" type="image/svg+xml">
<link rel="preload" href="{font_display}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{font_body}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css_fonts}">
<link rel="stylesheet" href="{css_style}">
<link rel="stylesheet" href="{css_categories}">
{json_ld}
<script defer src="{js_site}"></script>
{extra_js}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header}
<main id="main">
{body}
</main>
{footer}
</body>
</html>
"""


def header(ctx: components.Context, active: str = "") -> str:
    links = []
    for item in ctx.site.get("nav", []):
        current = ' aria-current="page"' if item.get("href") == active else ""
        links.append(f'<a href="{util.esc(ctx.link(item["href"]))}"{current}>{util.esc(item["label"])}</a>')
    repo = ctx.site.get("repo", "")
    github = (
        f'<a class="icon-button" href="{util.esc(repo)}" target="_blank" rel="noopener noreferrer"'
        f' aria-label="Source on GitHub" title="Source on GitHub">{icons.icon("github", size=18)}</a>'
        if repo
        else ""
    )
    return f"""<header class="site-header">
  <div class="wrap site-header__inner">
    <a class="brand" href="{util.esc(ctx.link('/'))}">
      <span class="brand__mark" aria-hidden="true">L/</span>
      <span>learners<span class="brand__tld">.ai</span></span>
    </a>
    <button type="button" class="icon-button nav-toggle" data-nav-toggle aria-expanded="false"
            aria-controls="site-nav" aria-label="Toggle navigation">{icons.icon('menu', size=18)}</button>
    <nav class="site-nav" id="site-nav" data-nav aria-label="Primary">
      {"".join(links)}
      {github}
    </nav>
  </div>
</header>"""


def footer(ctx: components.Context) -> str:
    registry = ctx.registry
    category_links = "".join(
        f'<li><a href="{util.esc(ctx.link(category.url))}">{util.esc(category.short_name)}</a></li>'
        for category in registry.populated_categories[:6]
    )
    role_links = "".join(
        f'<li><a href="{util.esc(ctx.link(role.url))}">{util.esc(role.name)}</a></li>'
        for role in sorted((r for r in registry.roles if r.tools), key=lambda r: r.name)[:6]
    )
    repo = ctx.site.get("repo", "")
    return f"""<footer class="site-footer">
  <div class="wrap site-footer__grid">
    <div>
      <h2>{util.esc(ctx.site.get("name", "learners.ai"))}</h2>
      <p class="small">{util.esc(ctx.site.get("description", ""))}</p>
      <p class="small muted">{util.esc(ctx.site.get("verification_disclaimer", ""))}</p>
    </div>
    <div>
      <h3>Categories</h3>
      <ul>{category_links}</ul>
    </div>
    <div>
      <h3>By role</h3>
      <ul>{role_links}</ul>
    </div>
    <div>
      <h3>Project</h3>
      <ul>
        <li><a href="{util.esc(ctx.link('/about/'))}">Method &amp; sources</a></li>
        <li><a href="{util.esc(ctx.link('/directory/'))}">Full directory</a></li>
        <li><a href="{util.esc(ctx.link('/categories/'))}">All categories</a></li>
        <li><a href="{util.esc(repo)}" target="_blank" rel="noopener noreferrer">GitHub repository</a></li>
      </ul>
    </div>
    <p class="site-footer__note">
      <span>Open source · {util.esc(ctx.site.get("license", "MIT"))} licensed</span>
      <span class="mono">Last pricing sweep: {util.esc(registry.last_verified)}</span>
      <span class="mono">{len(registry.tools)} tools · {len(registry.categories)} categories</span>
    </p>
  </div>
</footer>"""


def render_page(
    ctx: components.Context,
    *,
    title: str,
    description: str,
    path: str,
    body: str,
    active: str = "",
    og_type: str = "website",
    json_ld: Sequence[dict] | None = None,
    extra_js: Sequence[str] = (),
) -> str:
    """Assemble a full document. `path` is the root-absolute URL of the page."""
    canonical = ctx.absolute(path) if ctx.base_url else ""
    json_ld_tags = ""
    if json_ld:
        json_ld_tags = "\n".join(
            f'<script type="application/ld+json">{util.dumps(item, compact=True)}</script>' for item in json_ld
        )
    scripts = "\n".join(f'<script defer src="{util.esc(ctx.link(src))}"></script>' for src in extra_js)
    return SHELL.format(
        title=util.esc(title),
        description=util.esc(description),
        canonical=util.esc(canonical),
        og_type=util.esc(og_type),
        site_name=util.esc(ctx.site.get("name", "learners.ai")),
        favicon=util.esc(ctx.link("/assets/favicon.svg")),
        font_display=util.esc(ctx.link("/assets/fonts/space-grotesk-latin.woff2")),
        font_body=util.esc(ctx.link("/assets/fonts/ibm-plex-sans-latin.woff2")),
        css_fonts=util.esc(ctx.link("/assets/css/fonts.css")),
        css_style=util.esc(ctx.link("/assets/css/style.css")),
        css_categories=util.esc(ctx.link("/assets/css/categories.css")),
        js_site=util.esc(ctx.link("/assets/js/site.js")),
        extra_js=scripts,
        json_ld=json_ld_tags,
        header=header(ctx, active),
        body=body,
        footer=footer(ctx),
    )
