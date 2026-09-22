# learners.ai

learners.ai is a static, zero-dependency reference site for AI tools used in professional work. The project keeps all tool data in JSON files and builds a set of static HTML pages from those files so the site can be versioned, reviewed, and published without a backend or build toolchain.

## Project goals

- Build static reference pages for AI tools across categories
- Keep pricing and metadata in structured JSON instead of hardcoded HTML
- Provide a maintainable generator that can be rerun as tools change
- Keep the site fast, accessible, and easy to host on GitHub Pages or any static host

## Structure

- `data/` — site metadata, category taxonomy, and tool entries
- `generator/` — schema validation, data loading, and page rendering logic
- `assets/` — CSS, JS, fonts, and static assets
- `scripts/` — build, font-fetch, and link-check utilities
- `site/` — generated output directory created by the build process

## Build the site

```bash
python3 scripts/build.py
```

This writes the generated static site into `site/`.

## Validate the project

```bash
python3 -m compileall generator scripts
python3 scripts/check_links.py
```

The link-check utility is intentionally conservative: some vendor sites block automated HEAD/GET probes, so a failed check can reflect ant-bot protection rather than a dead URL.

## Add a new tool

1. Open the relevant category file in `data/tools/`.
2. Add a JSON object following the tool schema used by the generator.
3. Ensure the `category` matches the category id, `who_uses_it` matches entries in `data/roles.json`, and `platform` matches entries in `data/platforms.json`.
4. Run the generator again:

```bash
python3 scripts/build.py
```

## Notes on maintenance

- Keep `pricing_last_verified` up to date whenever pricing or plans change.
- Prefer legitimate, public product URLs over placeholders.
- Use `needs_verification` for entries that still need a human check.
- Keep descriptions original and practical rather than copied vendor marketing copy.
