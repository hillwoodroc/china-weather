import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from china_weather import provider, storage, __version__


class UserAgentTests(unittest.TestCase):
    def test_default_and_saved_preferences_apply_to_requests(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(storage, 'SETTINGS', Path(directory) / 'settings.json'):
            response = Mock()
            response.read.return_value = b'{}'
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            with patch.object(provider, 'urlopen', return_value=response) as open_url:
                for setting, expected in [(None, provider.BROWSER_USER_AGENT),
                                          (False, f'ChinaWeather/{__version__}'),
                                          (True, provider.BROWSER_USER_AGENT)]:
                    if setting is not None:
                        storage.save(storage.SETTINGS, {'browser_user_agent': setting})
                    provider.fetch('https://www.weather.com.cn/')
                    request = open_url.call_args.args[0]
                    self.assertEqual(request.get_header('User-agent'), expected)
                    self.assertEqual(request.get_header('Referer'), 'https://www.weather.com.cn/')

    def test_presets_custom_and_other_preferences(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(storage, 'SETTINGS', Path(directory) / 'settings.json'):
            storage.save(storage.SETTINGS, {'language': 'zh_TW', 'auto_location': True})
            for preset, expected in provider.USER_AGENTS.items():
                provider.save_user_agent(preset)
                self.assertEqual(provider.user_agent(), expected)
            provider.save_user_agent('custom', ' MyBrowser/1.0 ')
            self.assertEqual(provider.user_agent(), 'MyBrowser/1.0')
            settings = storage.load(storage.SETTINGS, {})
            self.assertEqual(settings['language'], 'zh_TW')
            self.assertTrue(settings['auto_location'])

    def test_reject_invalid_custom_headers_and_fallback(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(storage, 'SETTINGS', Path(directory) / 'settings.json'):
            for value in ('', '  ', 'Browser/1.0\r\nX-Test: yes', '浏览器', 'a' * 1025):
                with self.assertRaises(ValueError):
                    provider.save_user_agent('custom', value)
            with self.assertRaises(ValueError):
                provider.save_user_agent('unknown')
            storage.save(storage.SETTINGS, {'user_agent_preset': 'custom', 'custom_user_agent': '\n'})
            self.assertEqual(provider.user_agent(), provider.BROWSER_USER_AGENT)
