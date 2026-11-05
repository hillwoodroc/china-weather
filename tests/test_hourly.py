import json
from pathlib import Path
import unittest
from unittest.mock import patch
from china_weather import provider

FIXTURE = Path(__file__).parent / 'fixtures' / 'hourly.html'


class HourlyTests(unittest.TestCase):
    def test_actual_page_forecast_fields(self):
        data = provider.parse_hourly(FIXTURE.read_text())
        self.assertEqual(data['updated'], '2026-10-31 11:30')
        self.assertEqual(len(data['rows']), 8)
        self.assertEqual(data['rows'][0], dict(time='31日11时', condition='小雨',
                                             temperature='19℃', direction='北风', wind='<3级'))

    def test_actual_page_observations_midnight_and_repeated_hour(self):
        data = provider.parse_observations(FIXTURE.read_text())
        self.assertEqual(len(data['rows']), 25)
        self.assertEqual(data['rows'][0]['time'], '10-30 14:00')
        self.assertEqual(data['rows'][-1]['time'], '10-31 14:00')
        self.assertEqual(data['rows'][-1]['humidity'], 92)
        self.assertEqual(data['rows'][-1]['rain'], .1)
        self.assertEqual(data['rows'][-1]['wind'], 1)
        self.assertEqual(data['rows'][-1]['temperature'], 18.3)

    def test_missing_zero_negative_and_year_boundary(self):
        raw = {'od': {'od0': '202601010000', 'od2': [
            {'od21': '00', 'od22': '-2', 'od26': '0', 'od25': '', 'od27': '9999'},
            {'od21': '23', 'od22': 'NaN', 'od26': 'null', 'od25': '1', 'od27': '95'}]}}
        data = provider.parse_observations('<script>var observe24h_data = ' + json.dumps(raw) + '</script>')
        self.assertEqual(data['rows'][0]['time'], '12-31 23:00')
        self.assertIsNone(data['rows'][0]['temperature'])
        self.assertEqual(data['rows'][1]['temperature'], -2)
        self.assertEqual(data['rows'][1]['rain'], 0)
        self.assertIsNone(data['rows'][1]['humidity'])
        self.assertIsNone(data['rows'][1]['wind'])

    def test_partial_failure_preserves_other_section(self):
        html = FIXTURE.read_text().replace('var observe24h_data', 'var unavailable')
        with patch.object(provider, 'fetch', return_value=html):
            data = provider.details(provider.City('101040100', '重庆'))
        self.assertEqual(len(data['hourly']['rows']), 8)
        self.assertIn('observations_error', data)

    def test_missing_or_executable_assignment_not_evaluated(self):
        for html in ['<p>no data</p>', '<script>var hour3data = alert(1)</script>']:
            with self.assertRaises(ValueError):
                provider.parse_hourly(html)
