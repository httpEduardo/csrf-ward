import argparse
import re
import sys

FORM_RE = re.compile(r"<form\b[^>]*>(.*?)</form>", re.IGNORECASE | re.DOTALL)
ACTION_RE = re.compile(r"action=\"([^\"]*)\"|action='([^']*)'", re.IGNORECASE)
METHOD_RE = re.compile(r"method=\"([^\"]*)\"|method='([^']*)'", re.IGNORECASE)
TOKEN_RE = re.compile(r"name=\"(csrf|csrf_token|_csrf|xsrf)\"|name='(csrf|csrf_token|_csrf|xsrf)'", re.IGNORECASE)


def parse_forms(html: str) -> list[dict[str, str]]:
    forms = []
    for match in FORM_RE.finditer(html):
        block = match.group(0)
        action_match = ACTION_RE.search(block)
        method_match = METHOD_RE.search(block)
        action = action_match.group(1) or action_match.group(2) if action_match else ""
        method = method_match.group(1) or method_match.group(2) if method_match else "get"
        has_token = TOKEN_RE.search(block) is not None
        forms.append({
            "action": action,
            "method": method.lower(),
            "token": "yes" if has_token else "no",
        })
    return forms


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan HTML forms for CSRF tokens.")
    parser.add_argument("--input", required=True, help="HTML file to scan")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as handle:
            html = handle.read()
    except OSError as exc:
        print(f"Failed to read {args.input}: {exc}", file=sys.stderr)
        return 1

    forms = parse_forms(html)
    if not forms:
        print("No forms found.")
        return 0

    missing = 0
    for idx, form in enumerate(forms, start=1):
        action = form["action"] or "(no action)"
        status = "ok" if form["token"] == "yes" or form["method"] == "get" else "missing"
        if status == "missing":
            missing += 1
        print(f"Form {idx}: {form['method'].upper()} {action} -> {status}")

    print(f"\nForms scanned: {len(forms)}")
    print(f"Forms missing CSRF token: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
