import unittest
from types import SimpleNamespace
from china_weather.charts import TrendChart


class ChartTests(unittest.TestCase):
    def test_hover_selects_nearest_hour_including_endpoints(self):
        chart = SimpleNamespace(rows=[{}, {}, {}])
        for x, expected in [(65, 0), (89, 0), (91, 1), (115, 1), (165, 2)]:
            self.assertEqual(TrendChart.index_at(chart, x, 50, 185, 210), expected)
        for x, y in [(64, 50), (166, 50), (100, 19), (100, 169)]:
            self.assertIsNone(TrendChart.index_at(chart, x, y, 185, 210))

    def test_empty_and_single_hour(self):
        self.assertIsNone(TrendChart.index_at(SimpleNamespace(rows=[]), 65, 50, 185, 210))
        self.assertEqual(TrendChart.index_at(SimpleNamespace(rows=[{}]), 115, 50, 185, 210), 0)

    def test_leave_clears_highlight(self):
        calls = []
        chart = SimpleNamespace(hover_index=1, queue_draw=lambda: calls.append(True))
        TrendChart.pointer_leave(chart, None)
        self.assertIsNone(chart.hover_index)
        self.assertEqual(calls, [True])
