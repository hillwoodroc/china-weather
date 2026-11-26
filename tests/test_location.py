import unittest
from unittest.mock import patch
from china_weather.provider import City, parse_location, locate


class LocationTests(unittest.TestCase):
    def test_live_response_shape_and_duplicate_names(self):
        payload = 'var ip="192.0.2.1";var id="101043500";var addr="重庆,大渡口,大渡口";'
        self.assertEqual(parse_location(payload), City('101043500', '大渡口', '重庆'))

    def test_municipality_and_province(self):
        self.assertEqual(parse_location('var id="101010100";var addr="北京,北京,北京";'), City('101010100', '北京'))
        self.assertEqual(parse_location('var id="101210101";var addr="浙江,杭州";'), City('101210101', '杭州', '浙江'))

    def test_invalid_unsupported_and_executable_responses(self):
        for payload in ('<html>blocked</html>', 'var id="foreign";var addr="London";',
                        'var id="101010100";var addr="";',
                        'var id=alert(1);var addr="北京";'):
            with self.assertRaises(ValueError):
                parse_location(payload)

    def test_request_and_error_propagation(self):
        with patch('china_weather.provider.fetch', return_value='var id="101010100";var addr="北京";') as fetch:
            self.assertEqual(locate().code, '101010100')
            self.assertTrue(fetch.call_args.args[0].startswith('https://wgeo.weather.com.cn/ip/?_='))
        with patch('china_weather.provider.fetch', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                locate()


class LocationFlowTests(unittest.TestCase):
    def window(self):
        from types import SimpleNamespace, MethodType
        from unittest.mock import Mock
        from china_weather.app import Window
        w = SimpleNamespace(location_serial=0, search_serial=0, search_timer=None,
                            locate_button=Mock(), search_status=Mock(), search=Mock(),
                            location_popover=Mock(), add_city=Mock(), async_call=Mock())
        w.cancel_location = MethodType(Window.cancel_location, w)
        w.start = MethodType(Window.locate_city, w)
        return w

    def test_detect_select_and_error(self):
        w = self.window()
        w.start()
        w.locate_button.set_sensitive.assert_called_with(False)
        _, done = w.async_call.call_args.args
        city = City('101010100', '北京')
        done(city, None)
        w.add_city.assert_called_once_with(city)
        w.locate_button.set_sensitive.assert_called_with(True)
        w.start()
        _, done = w.async_call.call_args.args
        done(None, 'offline')
        self.assertEqual(w.add_city.call_count, 1)
        w.location_popover.popup.assert_called_once()

    def test_manual_selection_cancels_old_location_result(self):
        w = self.window()
        w.start()
        _, done = w.async_call.call_args.args
        w.cancel_location()
        done(City('101010100', '北京'), None)
        w.add_city.assert_not_called()
