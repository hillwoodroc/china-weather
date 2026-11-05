import ast
import gettext
from pathlib import Path
import string
import unittest
from china_weather import i18n


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language('system')

    def test_locale_priority_and_variants(self):
        for locale, expected in [('zh_CN.UTF-8', 'zh_CN'), ('zh_SG', 'zh_CN'),
                                 ('zh-Hant', 'zh_TW'), ('zh_HK.UTF-8', 'zh_TW'),
                                 ('zh_TW', 'zh_TW'), ('en_US', 'en'), ('fr_FR', 'en')]:
            self.assertEqual(i18n.system_language({'LANG': locale}), expected)
        self.assertEqual(i18n.system_language({'LANG': 'zh_CN', 'LC_ALL': 'en_US'}), 'en')
        self.assertEqual(i18n.system_language({'LANG': 'en_US', 'LANGUAGE': 'zh_TW:en'}), 'zh_TW')
        self.assertEqual(i18n.system_language({'LANG': 'C', 'LANGUAGE': 'zh_TW'}), 'en')

    def test_catalog_coverage_and_format_fields(self):
        formatter = string.Formatter()
        for language in ('zh_CN', 'zh_TW', 'en'):
            catalog = gettext.translation(i18n.DOMAIN, localedir=i18n.LOCALEDIR,
                                          languages=[language])
            for source in i18n.MESSAGES:
                self.assertIn(source, catalog._catalog)
                translated = catalog.gettext(source)
                self.assertTrue(translated)
                fields = {field for _, field, _, _ in formatter.parse(source) if field}
                self.assertEqual(fields, {field for _, field, _, _ in formatter.parse(translated) if field})
            for source in i18n.WEATHER:
                self.assertIn('weather\x04' + source, catalog._catalog)
        for path in Path('china_weather').glob('*.py'):
            if path.name == 'i18n.py':
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_':
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.assertIn(node.args[0].value, i18n.MESSAGES)

    def test_context_keeps_wind_unit_separate(self):
        i18n.set_language('en')
        self.assertEqual(i18n.translate('级'), 'Beaufort')
        self.assertEqual(i18n.weather_text('3级'), '3 Bft')

    def test_weather_errors_and_raw_data(self):
        raw = '小雨转多云'
        i18n.set_language('en')
        self.assertEqual(i18n.weather_text(raw), 'Light rain → Cloudy')
        self.assertEqual(i18n.weather_text('东北风3-4级'), 'NE wind3-4 Bft')
        self.assertEqual(i18n.error_text('页面没有提供 hour3data 数据'), 'The page does not provide hour3data data')
        self.assertEqual(i18n.translate('优'), 'Good')
        i18n.set_language('zh_TW')
        self.assertEqual(i18n.weather_text(raw), '小雨轉多雲')
        self.assertEqual(i18n.translate('刷新天气'), '重新整理天氣')
        i18n.set_language('zh_CN')
        self.assertEqual(i18n.weather_text(raw), raw)
        self.assertEqual(i18n.translate('unknown'), 'unknown')
