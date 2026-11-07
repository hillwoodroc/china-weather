import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from china_weather.app import Window
from china_weather.i18n import translate as _
from china_weather.provider import City


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.window = SimpleNamespace(
            search_serial=0, search_timer=None, cities=[],
            search=Mock(), search_status=Mock(), results=Mock(),
            show_cities=Mock(), async_call=Mock())
        self.window.results.get_first_child.return_value = None

    def search(self, query):
        self.window.search.get_text.return_value = query
        with patch('china_weather.app.GLib.timeout_add', return_value=123) as timer:
            Window.search_changed(self.window, self.window.search)
        return timer

    def test_empty_search_shows_saved_cities(self):
        self.search('')
        self.window.search_status.set_text.assert_called_with(_('收藏城市'))
        self.window.show_cities.assert_called_once_with([])

    def test_search_results_and_error(self):
        timer = self.search('北京')
        self.window.search_status.set_text.assert_called_with(_('正在搜索…'))
        timer.call_args.args[1]()
        work, done = self.window.async_call.call_args.args
        cities = [City('101010100', '北京')]
        with patch('china_weather.app.provider.search', return_value=cities) as search:
            self.assertEqual(work(), cities)
            search.assert_called_once_with('北京')
        done(cities, None)
        self.window.search_status.set_text.assert_called_with(_('搜索结果'))
        self.window.show_cities.assert_called_with(cities)
        done([], None)
        self.window.search_status.set_text.assert_called_with(_('没有找到城市'))
        done(None, 'offline')
        self.window.search_status.set_text.assert_called_with(_('搜索失败：') + 'offline')

    def test_city_code_search(self):
        timer = self.search('101010100')
        timer.call_args.args[1]()
        self.window.search_status.set_text.assert_called_with(_('按城市代码查询'))
        self.window.show_cities.assert_called_once_with([City('101010100', '101010100')])
        self.window.async_call.assert_not_called()
