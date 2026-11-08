import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from china_weather import __version__
from china_weather.app import Application
from china_weather.i18n import translate


class AboutTests(unittest.TestCase):
    def test_native_about_keeps_website_on_main_page(self):
        for kind in ('AboutDialog', 'AboutWindow'):
            with self.subTest(kind=kind):
                about = Mock()
                app = SimpleNamespace(get_windows=lambda: [])
                with patch('china_weather.app.Adw', SimpleNamespace(**{kind: about})):
                    Application.show_about(app, Mock(), None)
                properties = about.call_args.kwargs
                self.assertEqual(properties['application_name'], translate('中国天气'))
                self.assertEqual(properties['website'], 'https://github.com/hillwoodroc/china-weather')
                self.assertEqual(properties['issue_url'], 'https://github.com/hillwoodroc/china-weather/issues')
                self.assertEqual(properties['developers'], ['Hillwood Yang'])
                self.assertEqual(properties['version'], __version__)
                self.assertEqual(__version__, '1.0')
                self.assertNotIn('comments', properties)
                about.return_value.present.assert_called_once_with(*([None] if kind == 'AboutDialog' else []))

    def test_legacy_gtk_fallback(self):
        app = SimpleNamespace(get_windows=lambda: [])
        with patch('china_weather.app.Adw', SimpleNamespace()), patch('china_weather.app.Gtk.AboutDialog') as about:
            Application.show_about(app, Mock(), None)
        self.assertEqual(about.call_args.kwargs['website_label'], translate('网站'))
        self.assertEqual(about.call_args.kwargs['version'], __version__)
        about.return_value.present.assert_called_once_with()
