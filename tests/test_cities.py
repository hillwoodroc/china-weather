import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from china_weather import storage
from china_weather.app import Adw, Gdk, Gtk, Window
from china_weather.provider import City


Gtk.init_check()


@unittest.skipUnless(Gdk.Display.get_default(), 'GTK display required')
class CitySwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id='io.github.hillwood.ChinaWeather.Tests')
        cls.app.register(None)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        for name, path in [('CONFIG', root / 'cities.json'),
                           ('SETTINGS', root / 'settings.json'), ('CACHE', root / 'cache')]:
            patcher = patch.object(storage, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.requests = []
        patcher = patch.object(Window, 'async_call',
                               lambda window, work, done: self.requests.append(done))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.beijing = City('101010100', '北京')
        self.chongqing = City('101040100', '重庆')

    def window(self):
        window = Window(self.app)
        self.addCleanup(window.destroy)
        self.addCleanup(window.closed)
        return window

    def test_add_switch_restore_and_remove(self):
        storage.save(storage.SETTINGS, {'language': 'en'})
        window = self.window()
        window.add_city(self.beijing)
        window.add_city(self.chongqing)
        window.add_city(City(self.beijing.code, 'Beijing'))
        self.assertEqual(window.cities, [self.beijing, self.chongqing])
        window.search.set_text('')
        window.show_cities(window.cities)
        button = window.results.get_first_child().get_next_sibling()
        button.emit('clicked')
        self.assertEqual(window.city, self.chongqing)
        self.assertEqual(window.city_label.get_text(), self.chongqing.name)
        self.assertFalse(window.results.get_first_child().get_child().get_last_child().get_visible())
        self.assertTrue(window.results.get_first_child().get_next_sibling().get_child().get_last_child().get_visible())
        self.assertEqual(storage.load(storage.CONFIG, []),
                         [asdict(self.beijing), asdict(self.chongqing)])
        self.assertEqual(storage.load(storage.SETTINGS, {})['language'], 'en')
        restored = self.window()
        self.assertEqual(restored.city, self.chongqing)
        restored.toggle_favorite()
        restored.select(self.beijing)
        self.assertEqual(restored.cities, [self.beijing])
        self.assertEqual(storage.load(storage.CONFIG, []), [asdict(self.beijing)])

    def test_previous_city_response_cannot_replace_selected_city(self):
        window = self.window()
        window.add_city(self.beijing)
        old_response = self.requests[-1]
        window.add_city(self.chongqing)
        old_response(None, 'old request failed')
        self.assertEqual(window.city, self.chongqing)
        self.assertFalse(window.refresh.get_sensitive())
        self.requests[-1](None, 'request failed')
        self.assertTrue(window.refresh.get_sensitive())
