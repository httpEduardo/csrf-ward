import unittest

from csrf_ward import scan_html


def statuses(html):
    return [f.status for f in scan_html(html)]


class ScanTests(unittest.TestCase):
    def test_post_without_token(self):
        self.assertEqual(statuses('<form method="post" action="/x"><input name="a"></form>'), ["missing"])

    def test_framework_tokens(self):
        for name in ["csrfmiddlewaretoken", "authenticity_token", "__RequestVerificationToken", "_token"]:
            html = f'<form method="post"><input type="hidden" name="{name}" value="t"></form>'
            self.assertEqual(statuses(html), ["ok"], name)

    def test_empty_token(self):
        self.assertEqual(statuses('<form method="post"><input name="csrf" value=""></form>'), ["empty-token"])

    def test_method_is_case_insensitive(self):
        self.assertEqual(statuses('<form method="POST"></form>'), ["missing"])

    def test_plain_get_is_fine_but_sensitive_get_is_not(self):
        self.assertEqual(statuses('<form action="/search"></form>'), ["ok"])
        self.assertEqual(statuses('<form action="/logout" method="get"></form>'), ["state-changing-get"])

    def test_method_override(self):
        html = '<form method="post"><input name="_method" value="DELETE"></form>'
        forms = scan_html(html)
        self.assertEqual(forms[0].method, "delete")
        self.assertEqual(forms[0].status, "missing")

    def test_line_numbers(self):
        forms = scan_html("<html>\n\n<form method='post'></form>")
        self.assertEqual(forms[0].line, 3)


if __name__ == "__main__":
    unittest.main()
