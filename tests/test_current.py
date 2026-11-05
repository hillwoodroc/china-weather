import unittest
from unittest.mock import patch
from china_weather.provider import parse_current, current, City, aqi_description


class CurrentTests(unittest.TestCase):
    def test_current_fields_are_observations(self):
        payload = 'var dataSK={"city":"101040100","weather":"晴","temp":"16.4","SD":"81%","WD":"东北风","WS":"1级","aqi":"30","date":"11月01日(星期日)","time":"21:20"}'
        data = parse_current(payload)
        self.assertEqual(data['condition'], '晴')
        self.assertEqual(data['temperature'], 16.4)
        self.assertEqual(data['humidity'], 81)
        self.assertEqual(data['direction'], '东北风')
        self.assertEqual(data['wind'], '1级')
        self.assertEqual(data['aqi'], 30)
        self.assertEqual(data['updated'], '11月01日(星期日) 21:20')

    def test_missing_fields_do_not_become_zero(self):
        data = parse_current('var dataSK={"city":"101040100","temp":"9999","SD":"","aqi":""}')
        for key in ('temperature', 'humidity', 'aqi'):
            self.assertIsNone(data[key])
        data = parse_current('var dataSK={"city":"101040100","temp":"-2","SD":"0%","aqi":"0"}')
        self.assertEqual(data['temperature'], -2)
        self.assertEqual(data['humidity'], 0)
        self.assertEqual(data['aqi'], 0)

    def test_wrong_city_and_bad_payload(self):
        with patch('china_weather.provider.fetch', return_value='var dataSK={"city":"101010100"}'):
            with self.assertRaisesRegex(ValueError, '不匹配'):
                current(City('101040100', '重庆'))
        with self.assertRaises(ValueError):
            parse_current('var dataSK=alert(1)')

    def test_aqi_boundaries(self):
        for value, expected in [(0,'优'), (50,'优'), (51,'良'), (100,'良'), (101,'轻度污染'),
                                (151,'中度污染'), (201,'重度污染'), (301,'严重污染'), (None,'暂无数据')]:
            self.assertEqual(aqi_description(value), expected)
