import unittest
from china_weather.temperature import convert_temperature, format_temperature


class TemperatureTests(unittest.TestCase):
    def test_freezing_boiling_and_negative_values(self):
        for value, expected in [(0, 32), (100, 212), (-40, -40), (20.5, 68.9)]:
            self.assertAlmostEqual(convert_temperature(value, 'fahrenheit'), expected)
            self.assertEqual(convert_temperature(value), value)

    def test_provider_strings_and_missing_values(self):
        for raw in ('20℃', '20°C', '20°', '20'):
            self.assertEqual(format_temperature(raw, 'fahrenheit'), '68°F')
        for raw in (None, '', '—', 'nan', 'inf'):
            self.assertEqual(format_temperature(raw), '—')
        self.assertEqual(format_temperature('0℃'), '0°C')
