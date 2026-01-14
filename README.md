# CSRF Ward

CSRF Ward scans HTML files for forms missing CSRF tokens.

## Quick start

```bash
python csrf_ward.py --input pages.html
```

## Output

Each form is listed with its action and whether a CSRF token was detected.
