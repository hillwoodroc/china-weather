import unittest
from china_weather.provider import parse_forecast, parse_search, City


class ParserTests(unittest.TestCase):
    def test_day_and_night_missing_high(self):
        html = '''<div id="7d"><ul><li><h1>30日（今天）</h1>
        <p class="wea">多云转小雨</p><p class="tem"><span>20</span>/<i>15℃</i></p>
        <p class="win"><em><span title="北风"></span></em><i>&lt;3级</i></p></li>
        <li><h1>31日</h1><p class="wea">小雨</p><p class="tem"><i>-2℃</i></p></li></ul></div>
        <li><h1>广告</h1></li>'''
        days = parse_forecast(html)
        self.assertEqual(len(days), 2)
        self.assertEqual(days[0]['high'], '20')
        self.assertEqual(days[0]['wind'], '<3级')
        self.assertIsNone(days[1]['high'])
        self.assertEqual(days[1]['low'], '-2℃')

    def test_changed_page_fails_explicitly(self):
        with self.assertRaises(ValueError):
            parse_forecast('<html>Access denied</html>')

    def test_jsonp_search_validation_and_dedup(self):
        cities = parse_search('callback([{"ref":"101040100~重庆~chongqing"}, {"ref":"101040100~重庆"}, {"ref":"../../etc"}, {"ref":"101010100","name":"北京"}]);')
        self.assertEqual(cities, [City('101040100', '重庆'), City('101010100', '北京')])

    def test_search_code_in_separate_id(self):
        self.assertEqual(parse_search('[{"id":"101040100","name":"重庆","ref":"重庆~chongqing"}]'),
                         [City('101040100', '重庆')])

    def test_search_code_after_name(self):
        self.assertEqual(parse_search('success_jsonpCallback([{"ref":"重庆~chongqing~101040100"}])'),
                         [City('101040100', '重庆')])

    def test_search_nested_ref(self):
        import json
        for ref in ({'cityCode': '101040100', 'cityName': '重庆'},
                    json.dumps({'cityCode': '101040100', 'cityName': '重庆'})):
            self.assertEqual(parse_search(json.dumps([{'ref': ref}])), [City('101040100', '重庆')])

    def test_unrecognized_response_is_not_empty_result(self):
        with self.assertRaisesRegex(ValueError, '未能识别'):
            parse_search('[{"unexpected":"value"}]')
        self.assertEqual(parse_search('success_jsonpCallback([])'), [])

    def test_search_request_callback_and_encoding(self):
        from unittest.mock import patch
        from urllib.parse import urlparse, parse_qs
        from china_weather.provider import search
        with patch('china_weather.provider.fetch', return_value='success_jsonpCallback([])') as fetch:
            self.assertEqual(search(' 重庆 '), [])
        url = urlparse(fetch.call_args.args[0])
        self.assertEqual(url.scheme, 'https')
        self.assertEqual(url.hostname, 'toy1.weather.com.cn')
        self.assertEqual(url.path, '/search')
        params = parse_qs(url.query)
        self.assertEqual(params['cityname'], ['重庆'])
        self.assertEqual(params['callback'], ['success_jsonpCallback'])

    def test_no_script_execution(self):
        with self.assertRaises(ValueError):
            parse_search('alert(1)')


if __name__ == '__main__':
    unittest.main()
