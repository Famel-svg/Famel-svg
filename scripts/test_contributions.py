import unittest
from xml.etree import ElementTree
from update_contributions import parse_calendar, render


class CalendarTest(unittest.TestCase):
    def test_calendar_and_svg(self):
        html = '<td id="contribution-day-component-0-0" data-date="2026-10-04" data-level="4"></td><tool-tip for="contribution-day-component-0-0">1,234 contributions on October 4th.</tool-tip><td id="contribution-day-component-1-0" data-date="2026-10-05" data-level="0"></td><tool-tip for="contribution-day-component-1-0">No contributions on October 5th.</tool-tip>'
        days = parse_calendar(html)
        self.assertEqual([count for _, _, count in days], [1234, 0])
        self.assertIn('1234 contribuições', render(days))
        ElementTree.fromstring(render(days))
        for broken in [html.replace('2026-10-05', '2026-10-06'), html.replace('data-level="4"', 'data-level="0"'), '<html>Unavailable</html>']:
            with self.assertRaises(ValueError):
                parse_calendar(broken)


if __name__ == '__main__':
    unittest.main()
