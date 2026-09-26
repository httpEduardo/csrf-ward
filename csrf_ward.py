"""Scan HTML files for state-changing forms that lack a CSRF token."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Field names used by common frameworks for anti-CSRF tokens.
TOKEN_NAMES = {
    "csrf", "csrf_token", "csrftoken", "_csrf", "_csrf_token", "xsrf", "_xsrf", "xsrf_token",
    "csrfmiddlewaretoken",         # Django
    "authenticity_token",          # Rails
    "__requestverificationtoken",  # ASP.NET
    "_token",                      # Laravel
    "anti-csrf-token",
}

STATE_CHANGING = {"post", "put", "patch", "delete"}

# Actions that change state even though the form uses GET.
SENSITIVE_GET = re.compile(r"(delete|remove|logout|transfer|pay|update|reset|disable|approve)", re.IGNORECASE)


@dataclass
class Form:
    line: int
    action: str = ""
    method: str = "get"
    token: bool = False
    empty_token: bool = False
    fields: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.method in STATE_CHANGING:
            if self.token:
                return "ok"
            return "empty-token" if self.empty_token else "missing"
        if SENSITIVE_GET.search(self.action):
            return "state-changing-get"
        return "ok"


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[Form] = []
        self._current: Form | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "form":
            self._current = Form(
                line=self.getpos()[0],
                action=a.get("action", ""),
                method=(a.get("method") or "get").strip().lower(),
            )
            self.forms.append(self._current)
        elif tag in {"input", "button", "textarea", "select"} and self._current is not None:
            name = a.get("name", "")
            if name:
                self._current.fields.append(name)
            # Framework-style method override, e.g. <input name="_method" value="DELETE">
            if name.lower() == "_method" and a.get("value"):
                override = a["value"].strip().lower()
                if override in STATE_CHANGING:
                    self._current.method = override
            if name.lower() in TOKEN_NAMES:
                if a.get("value", "").strip():
                    self._current.token = True
                else:
                    self._current.empty_token = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._current = None


def scan_html(html: str) -> list[Form]:
    parser = FormParser()
    parser.feed(html)
    parser.close()
    return parser.forms


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find HTML forms that are missing CSRF protection.")
    parser.add_argument("paths", nargs="*", help="HTML files to scan")
    parser.add_argument("--input", "-i", action="append", default=[], help="HTML file to scan (repeatable)")
    args = parser.parse_args(argv)

    paths = args.paths + args.input
    if not paths:
        parser.error("provide at least one HTML file")

    problems = 0
    total = 0
    for path in paths:
        try:
            html = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2

        forms = scan_html(html)
        total += len(forms)
        print(f"{path}: {len(forms)} form(s)")
        for form in forms:
            status = form.status
            marker = "  ok     " if status == "ok" else "  ISSUE  "
            action = form.action or "(same page)"
            print(f"{marker}line {form.line:<4} {form.method.upper():<6} {action}  -> {status}")
            if status != "ok":
                problems += 1
        print()

    print(f"{total} form(s) scanned, {problems} issue(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
