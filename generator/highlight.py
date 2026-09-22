"""A deliberately small, dependency-free syntax highlighter.

Highlighting happens at build time (zero client JavaScript, zero shipped
highlighting library). It handles the five grammars this site actually uses -
shell, python, json, javascript and http - with a single-pass scanner that
finds strings, comments and numbers, then marks keywords and flags inside the
remaining plain text.

It is intentionally conservative: if a grammar is not recognised the content is
escaped and rendered as-is rather than mangled.
"""

from __future__ import annotations

import re
from typing import Iterable

_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&#39;"))

_LANGUAGES = {
    "bash": {
        "comment": r"#[^\n]*",
        "string": r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
        "number": r"\b\d+(?:\.\d+)?\b",
        "keywords": (
            "if", "then", "else", "fi", "for", "do", "done", "while", "export", "echo", "cd", "set",
            "source", "return", "function", "local", "curl", "pip", "npm", "git", "python3", "sudo",
        ),
        "flags": r"(?<=\s)--?[A-Za-z][\w-]*",
    },
    "python": {
        "comment": r"#[^\n]*",
        "string": r"\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
        "number": r"\b\d+(?:\.\d+)?\b",
        "keywords": (
            "def", "class", "return", "import", "from", "as", "if", "elif", "else", "for", "in", "with",
            "try", "except", "finally", "raise", "None", "True", "False", "and", "or", "not", "lambda",
            "async", "await", "yield", "print",
        ),
        "flags": None,
    },
    "javascript": {
        "comment": r"//[^\n]*|/\*[\s\S]*?\*/",
        "string": r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
        "number": r"\b\d+(?:\.\d+)?\b",
        "keywords": (
            "const", "let", "var", "function", "return", "if", "else", "for", "of", "in", "async",
            "await", "import", "export", "from", "new", "class", "extends", "try", "catch", "throw",
            "true", "false", "null", "undefined", "this",
        ),
        "flags": None,
    },
    "json": {
        "comment": None,
        "string": r"\"(?:\\.|[^\"\\])*\"",
        "number": r"(?<![\w\"])-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b",
        "keywords": ("true", "false", "null"),
        "flags": None,
    },
    "http": {
        "comment": r"#[^\n]*",
        "string": r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
        "number": r"\b\d{3}\b",
        "keywords": ("GET", "POST", "PUT", "PATCH", "DELETE", "HTTP", "Authorization", "Content-Type"),
        "flags": None,
    },
}

_ALIASES = {
    "sh": "bash",
    "shell": "bash",
    "console": "bash",
    "terminal": "bash",
    "py": "python",
    "js": "javascript",
    "ts": "javascript",
    "typescript": "javascript",
    "jsonc": "json",
    "rest": "http",
}

_SPAN = '<span class="tok--{kind}">{text}</span>'


def _escape(text: str) -> str:
    for char, entity in _ESCAPES:
        text = text.replace(char, entity)
    return text


def supported() -> list[str]:
    return sorted(_LANGUAGES)


def highlight(code: str, language: str = "") -> str:
    """Return HTML for `code`, tokenised when the language is known."""
    lang = _ALIASES.get((language or "").strip().lower(), (language or "").strip().lower())
    grammar = _LANGUAGES.get(lang)
    if not grammar or not code:
        return _escape(code)

    tokens: list[tuple[int, int, str]] = []
    taken: list[tuple[int, int]] = []

    def claim(pattern: str | None, kind: str) -> None:
        if not pattern:
            return
        for match in re.finditer(pattern, code):
            start, end = match.span()
            if any(start < t_end and end > t_start for t_start, t_end in taken):
                continue
            if start == end:
                continue
            taken.append((start, end))
            tokens.append((start, end, kind))

    claim(grammar["string"], "string")
    claim(grammar["comment"], "comment")
    claim(grammar["number"], "number")

    # Keywords and flags only outside strings/comments.
    interior = "".join(" " if any(s <= i < e for s, e in taken) else char for i, char in enumerate(code))
    for keyword in grammar["keywords"]:
        for match in re.finditer(rf"\b{re.escape(keyword)}\b", interior):
            tokens.append((match.start(), match.end(), "keyword"))
    if grammar["flags"]:
        for match in re.finditer(grammar["flags"], interior):
            tokens.append((match.start(), match.end(), "flag"))

    tokens.sort(key=lambda item: item[0])
    out: list[str] = []
    cursor = 0
    for start, end, kind in tokens:
        if start < cursor:
            continue
        out.append(_escape(code[cursor:start]))
        out.append(_SPAN.format(kind=kind, text=_escape(code[start:end])))
        cursor = end
    out.append(_escape(code[cursor:]))
    return "".join(out)


def highlight_lines(code: str, language: str = "") -> Iterable[str]:
    """Per-line highlighting, for the rare case a caller needs line numbers."""
    for line in code.splitlines():
        yield highlight(line, language)
