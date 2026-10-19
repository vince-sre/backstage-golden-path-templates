#!/usr/bin/env python3
"""Render a Scaffolder skeleton locally, the way fetch:template does.

Backstage uses Nunjucks with `${{ }}` for variables and `{% %}` for tags.
Jinja2 shares that syntax, so we configure it identically, register the
Nunjucks filters the skeletons use (dump, replace is builtin), and render file
contents *and* path names. StrictUndefined makes a typo in `values.x` fail.

    python3 scripts/render.py templates/python-service/skeleton out/ name=orders tier=tier-1 ...
"""

from __future__ import annotations

import json
import pathlib
import sys

import jinja2

ENV = jinja2.Environment(
    variable_start_string="${{",
    variable_end_string="}}",
    keep_trailing_newline=True,
    undefined=jinja2.StrictUndefined,
    autoescape=False,  # rendering source files, not HTML
)
ENV.filters["dump"] = json.dumps


def render_string(text: str, values: dict) -> str:
    return ENV.from_string(text).render(values=values)


def render_tree(skeleton: pathlib.Path, out: pathlib.Path, values: dict) -> list[pathlib.Path]:
    written = []
    for src in sorted(p for p in skeleton.rglob("*") if p.is_file()):
        rel = render_string(str(src.relative_to(skeleton)), values)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_string(src.read_text(encoding="utf-8"), values), encoding="utf-8")
        written.append(dest)
    return written


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    values = dict(kv.split("=", 1) for kv in argv[3:])
    files = render_tree(pathlib.Path(argv[1]), pathlib.Path(argv[2]), values)
    print(f"rendered {len(files)} files into {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
