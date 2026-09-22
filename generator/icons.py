"""Inline SVG icon set.

Icons are inlined rather than loaded as sprite files so that pages have no
extra network requests, icons inherit `currentColor` (so they pick up the
category accent automatically) and there is nothing to lazy-load or cache-bust.

Every icon is decorative: it is always accompanied by a text label, so
`aria-hidden="true"` is correct and screen readers will not announce them.
"""

from __future__ import annotations

# Stroke icons: 24x24 viewBox, drawn with currentColor.
_STROKE: dict[str, str] = {
    "chat": '<path d="M3.5 6.5A1.5 1.5 0 0 1 5 5h14a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 19 16H9.5L5.5 19v-3H5a1.5 1.5 0 0 1-1.5-1.5Z"/>',
    "code": '<path d="m9 8-4 4 4 4"/><path d="m15 8 4 4-4 4"/><path d="M13 5l-2 14"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="m5 18 5.5-5.5 3.5 3.5 3-3L21 16"/>',
    "video": '<rect x="2.5" y="6" width="13" height="12" rx="2"/><path d="m15.5 12 5.5-3.5v11Z"/>',
    "audio": '<path d="M3 12h2M7.5 7v10M12 4v16M16.5 8v8M21 11v2"/>',
    "pen": '<path d="M4 20h4l10-10a2.1 2.1 0 0 0-3-3L5 17Z"/><path d="m14.5 6.5 3 3"/>',
    "mic": '<rect x="9" y="3" width="6" height="10" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0"/><path d="M12 17.5V21"/>',
    "workflow": '<rect x="3" y="3.5" width="6" height="5" rx="1.5"/><rect x="15" y="15.5" width="6" height="5" rx="1.5"/><path d="M6 8.5V14a2 2 0 0 0 2 2h7"/>',
    "chart": '<path d="M4 4v16h16"/><path d="M8 16v-4M12.5 16V8M17 16v-2.5"/>',
    "slides": '<rect x="3.5" y="4.5" width="17" height="11" rx="1.5"/><path d="M12 15.5V20M8.5 20h7"/>',
    "design": '<path d="M12 3.5 20.5 12 12 20.5 3.5 12Z"/><circle cx="12" cy="12" r="2.5"/>',
    "megaphone": '<path d="M3.5 9.5h4L18 4v16l-10.5-5.5h-4Z"/><path d="m7.5 15.5 1 4.5h3l-1-4.5"/>',
    "headset": '<path d="M4.5 14v-2a7.5 7.5 0 0 1 15 0v2"/><rect x="2.5" y="13.5" width="4" height="6" rx="1.5"/><rect x="17.5" y="13.5" width="4" height="6" rx="1.5"/><path d="M19.5 19.5v.5a2 2 0 0 1-2 2H13"/>',
    "funnel": '<path d="M4 5h16l-6 7v6l-4 2v-8Z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "blocks": '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><path d="M17 13.5v7M13.5 17h7"/>',
    "server": '<rect x="3.5" y="4" width="17" height="6" rx="2"/><rect x="3.5" y="14" width="17" height="6" rx="2"/><path d="M7 7h.01M7 17h.01"/>',
    "users": '<circle cx="9" cy="8.5" r="3.5"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.5a3.5 3.5 0 0 1 0 7"/><path d="M21 20a6 6 0 0 0-4-5.6"/>',
    "scale": '<path d="M12 4v16M7 20h10M4 8h16"/><path d="M7 8 4 14h6Z"/><path d="M17 8l-3 6h6Z"/>',
    "shield": '<path d="M12 3.5 5 6v6c0 4 3 7.2 7 8.5 4-1.3 7-4.5 7-8.5V6Z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
    "dot": '<circle cx="12" cy="12" r="4"/>',
    # interface
    "external": '<path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M18 14.5V18.5A1.5 1.5 0 0 1 16.5 20h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M6 15h-.5A1.5 1.5 0 0 1 4 13.5v-8A1.5 1.5 0 0 1 5.5 4h8A1.5 1.5 0 0 1 15 5.5V6"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7"/>',
    "filter": '<path d="M4 6h16M7 12h10M10 18h4"/>',
    "star": '<path d="m12 4 2.4 5 5.6.8-4 3.9 1 5.5-5-2.7-5 2.7 1-5.5-4-3.9 5.6-.8Z"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
    "alert": '<path d="M12 4 2.5 20h19Z"/><path d="M12 10v4.5M12 17.5h.01"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "calendar-check": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M8 3.5v3M16 3.5v3M3.5 10h17M9 15l2 2 4-4"/>',
    "spark": '<path d="M12 3.5l1.8 4.7 4.7 1.8-4.7 1.8L12 16.5l-1.8-4.7L5.5 10l4.7-1.8Z"/><path d="M18.5 16.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9Z"/>',
}

# Filled icons (brand marks that must not be outlined).
_FILLED: dict[str, str] = {
    "github": (
        '<path fill="currentColor" stroke="none" d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.47-1.1-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.88 1.52 2.34 1.08 2.9.82.1-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.03A9.6 9.6 0 0 1 12 6.8c.85 0 1.7.12 2.5.34 1.9-1.3 2.74-1.03 2.74-1.03.55 1.38.2 2.4.1 2.65.64.7 1.03 1.6 1.03 2.69 0 3.85-2.35 4.7-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/>'
    ),
}


def available() -> list[str]:
    return sorted({*_STROKE, *_FILLED})


def icon(name: str, *, size: int = 24, css_class: str = "icon", width: float = 1.6) -> str:
    """Return an inline `<svg>` for `name`, falling back to the neutral dot."""
    key = (name or "").strip().lower()
    body = _STROKE.get(key) or _FILLED.get(key) or _STROKE["dot"]
    filled = key in _FILLED
    stroke = "" if filled else f' stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'
    return (
        f'<svg class="{css_class}" viewBox="0 0 24 24" width="{size}" height="{size}" '
        f'fill="none" stroke="currentColor"{stroke} aria-hidden="true" focusable="false">{body}</svg>'
    )
