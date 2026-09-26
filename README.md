# csrf-ward

`csrf-ward` scans rendered HTML files for forms that may change server-side state without a recognizable CSRF token. It helps review saved pages, template output, and crawler snapshots during development or security triage.

Cross-Site Request Forgery lets a malicious page submit a form to your site using the victim's session. The standard defense is a secret token embedded in every state-changing form. This tool checks rendered HTML — saved pages, templates output, or snapshots from a crawler — and reports the forms where that token is missing.

## What it reports

| Status | Meaning |
|--------|---------|
| `missing` | A `POST`/`PUT`/`PATCH`/`DELETE` form has no CSRF token field |
| `empty-token` | The token field exists but has no value (often a template bug) |
| `state-changing-get` | A `GET` form points at an action like `delete`, `logout`, `transfer` or `reset` — GET requests shouldn't change state and are usually not protected |
| `ok` | Nothing to report |

Token fields from common frameworks are recognized, including Django (`csrfmiddlewaretoken`), Rails (`authenticity_token`), ASP.NET (`__RequestVerificationToken`), Laravel (`_token`) and generic names like `csrf_token` or `_csrf`. Method overrides such as `<input name="_method" value="DELETE">` are taken into account.

## Usage

Requires Python 3.9 or later. No third-party packages are needed.

```bash
python csrf_ward.py pages.html
```

```text
pages.html: 6 form(s)
  ok     line 3    POST   /transfer  -> ok
  ISSUE  line 7    POST   /profile  -> missing
  ok     line 10   GET    /search  -> ok
  ISSUE  line 13   GET    /account/delete  -> state-changing-get
  ISSUE  line 16   POST   /settings  -> empty-token
  ok     line 20   DELETE /posts/42  -> ok

6 form(s) scanned, 3 issue(s)
```

Pass one or more files as positional arguments, or use the repeatable `--input` / `-i` option:

```bash
python csrf_ward.py site/*.html
python csrf_ward.py --input pages.html -i templates.html
```

The positional form is preferred; `--input` remains available for scripts that use the earlier interface.

Exit codes: `0` no issues, `1` at least one issue, `2` a file couldn't be read.

## Tests

```bash
python -m unittest
```

## Limitations

The tool only sees HTML. Applications that protect requests another way — a custom header added by JavaScript, `SameSite` cookies, or tokens injected at submit time — will show up as `missing` even though they're protected. Use the report as a checklist to verify, not as a final verdict.

## License

[MIT](LICENSE)
