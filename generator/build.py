from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from . import data, pages


def copy_assets(src_root: Path, out_root: Path) -> None:
    assets_src = src_root / "assets"
    assets_dst = out_root / "assets"
    if assets_src.exists():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)


def build_site(root: Path, output_dir: Path, *, strict: bool = False, only: list[str] | None = None) -> list[str]:
    registry = data.load(root, strict=strict, only=only)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(root, output_dir)

    def write(path: str, html: str) -> None:
        target = output_dir / path.strip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")

    write("index.html", pages.home_page(registry))
    write("categories/index.html", pages.all_categories_page(registry))
    write("directory/index.html", pages.directory_page(registry))
    write("roles/index.html", pages.roles_page(registry))
    write("about/index.html", pages.about_page(registry))

    for category in registry.categories:
        write(f"categories/{category.id}/index.html", pages.category_page(registry, category))

    for role in registry.roles:
        if role.count:
            write(f"roles/{role.slug}/index.html", pages.role_page(registry, role))

    for tool in registry.tools:
        write(f"tools/{tool.id}/index.html", pages.tool_page(registry, tool))

    return [f"{len(registry.tools)} tools across {len(registry.categories)} categories"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the static learners.ai site.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "site")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as validation errors.")
    parser.add_argument("--only", nargs="*", help="Restrict the build to specific category ids.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_site(args.root, args.output, strict=args.strict, only=args.only)
    print("✓ generated static site:", args.output)
    print(summary[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
