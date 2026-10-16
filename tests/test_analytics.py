import unittest
import xml.etree.ElementTree as ET
from scripts.update_analytics import parse_calendar, render


class AnalyticsTests(unittest.TestCase):
    def test_new_repository_changes_count_and_language_distribution(self):
        user = {'public_repos': 2, 'followers': 3, 'following': 4}
        repos = [{'name': 'one', 'language': 'Python', 'fork': False}]
        before = render(user, repos, (0, []), '17 Oct 2026')
        repos.append({'name': 'two', 'language': 'Rust', 'fork': False})
        after = render(dict(user, public_repos=3), repos, (0, []), '17 Oct 2026')
        self.assertIn('2 public repositories', before)
        self.assertIn('3 public repositories', after)
        self.assertIn('Rust  1 repos', after)
        ET.fromstring(after)

    def test_forks_do_not_inflate_language_chart_and_empty_account_renders(self):
        user = {'public_repos': 0, 'followers': 0, 'following': 0}
        svg = render(user, [{'name': 'fork', 'language': 'Java', 'fork': True}], (0, []), '17 Oct 2026')
        self.assertNotIn('Java', svg)
        self.assertIn('No language data yet', svg)
        ET.fromstring(svg)

    def test_calendar_reads_dates_and_levels_with_reordered_attributes(self):
        fixture = '''<h2>1,234 contributions in the last year</h2>
        <td data-level="3" id="contribution-day-component-2-51" data-date="2026-10-13" data-ix="51"></td>'''
        self.assertEqual(parse_calendar(fixture), (1234, [('2026-10-13', 2, 51, 3)]))

    def test_invalid_calendar_fails_instead_of_publishing_zero_activity(self):
        for page in ['<html>Sign in</html>', '<h2>123 contributions</h2>']:
            with self.subTest(page=page), self.assertRaises(ValueError):
                parse_calendar(page)


if __name__ == '__main__':
    unittest.main()
