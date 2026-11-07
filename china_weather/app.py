import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from zoneinfo import ZoneInfo
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, Gio, GLib, Gdk
from . import provider, storage
from .i18n import translate as _, weather_text, error_text, set_language, LANGUAGES
from .charts import TrendChart
from .widgets import ArrowScroller

POOL = ThreadPoolExecutor(max_workers=4)


def label(text, css=None):
    widget = Gtk.Label(label=text, wrap=True)
    if css:
        widget.add_css_class(css)
    return widget


def clear(box):
    while box.get_first_child():
        box.remove(box.get_first_child())


class Window(Adw.ApplicationWindow):
    def __init__(self, app, selected_city=None):
        super().__init__(application=app, title=_('中国天气'), default_width=940, default_height=720)
        self.city = None
        self.serial = self.search_serial = 0
        self.search_timer = None
        self.cities = []
        for item in storage.load(storage.CONFIG, []):
            try:
                city = provider.City(**item)
                if city not in self.cities:
                    self.cities.append(city)
            except (TypeError, ValueError):
                pass
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.content)
        header = self.header = Adw.HeaderBar()
        self.weather_stack = None
        self.tab_switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
        self.window_title = Adw.WindowTitle(title=_('中国天气'))
        header.set_title_widget(self.window_title)
        self.content.append(header)
        self.refresh = Gtk.Button(icon_name='view-refresh-symbolic', tooltip_text=_('刷新天气'))
        self.refresh.connect('clicked', lambda *_: self.select(self.city) if self.city else None)
        header.pack_end(self.refresh)
        self.star = Gtk.Button(icon_name='non-starred-symbolic', tooltip_text=_('收藏或取消收藏城市'))
        self.star.connect('clicked', self.toggle_favorite)
        header.pack_end(self.star)
        self.locations = Gtk.MenuButton(tooltip_text=_('选择地点'), halign=Gtk.Align.CENTER)
        self.locations.add_css_class('flat')
        location_title = Gtk.Box(spacing=6)
        self.city_label = label(_('选择地点'), 'heading')
        location_title.append(self.city_label)
        location_title.append(Gtk.Image.new_from_icon_name('pan-down-symbolic'))
        self.locations.set_child(location_title)
        language_menu = Gio.Menu()
        for code, name in LANGUAGES.items():
            language_menu.append(_('跟随系统') if code == 'system' else name,
                                 'app.language::' + code)
        self.language_button = Gtk.MenuButton(icon_name='preferences-desktop-locale-symbolic',
                                              tooltip_text=_('语言'), menu_model=language_menu)
        header.pack_end(self.language_button)
        self.location_popover = Gtk.Popover()
        self.locations.set_popover(self.location_popover)
        location_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                               width_request=300)
        for side in ('top', 'bottom', 'start', 'end'):
            getattr(location_box, 'set_margin_' + side)(12)
        self.location_popover.set_child(location_box)
        self.search = Gtk.SearchEntry(placeholder_text=_('搜索城市 / 拼音'))
        self.search.connect('search-changed', self.search_changed)
        location_box.append(self.search)
        self.location_popover.connect('notify::visible', self.locations_visible)
        self.search_status = label(_('收藏城市'), 'heading')
        location_box.append(self.search_status)
        self.results = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        location_scroll = ArrowScroller(self.results, vertical=True, height_request=260)
        location_box.append(location_scroll)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        for side in ('top', 'bottom', 'start', 'end'):
            getattr(self.body, 'set_margin_' + side)(8 if side in ('start', 'end') else 20)
        weather_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.locations.set_margin_top(12)
        weather_content.append(self.locations)
        weather_content.append(self.body)
        self.content.append(ArrowScroller(weather_content, vertical=True, vexpand=True))
        self.show_cities(self.cities)
        settings = storage.load(storage.SETTINGS, {})
        last_city = settings.get('selected_city') if isinstance(settings, dict) else None
        initial_city = next((c for c in self.cities if c.code == last_city), None)
        if selected_city or self.cities:
            self.select(selected_city or initial_city or self.cities[0])
        else:
            self.update_location_selector()
            self.empty(_('查看你关心的天气'), _('选择地点，查看当地天气和预报。'))
            choose = Gtk.Button(label=_('选择地点'), halign=Gtk.Align.CENTER)
            choose.add_css_class('suggested-action')
            choose.add_css_class('pill')
            choose.connect('clicked', lambda *_: self.locations.popup())
            self.body.append(choose)
        self.timer = GLib.timeout_add_seconds(1800, self.auto_refresh)
        self.connect('close-request', self.closed)

    def locations_visible(self, popover, *_):
        if popover.get_visible():
            self.search.grab_focus()
            if not self.search.get_text():
                self.show_cities(self.cities)

    def closed(self, *_):
        GLib.source_remove(self.timer)
        if self.search_timer:
            GLib.source_remove(self.search_timer)
        self.serial += 1
        self.search_serial += 1
        return False

    def auto_refresh(self):
        if self.city:
            self.select(self.city)
        return True

    def empty(self, title, description):
        self.header.set_title_widget(self.window_title)
        clear(self.body)
        status = Adw.StatusPage(title=title, description=description, icon_name='weather-few-clouds-symbolic')
        self.body.append(status)

    def async_call(self, work, done):
        def finished(future):
            try:
                result, error = future.result(), None
            except Exception as exc:
                result, error = None, error_text(exc)
            def dispatch():
                done(result, error)
                return False
            GLib.idle_add(dispatch)
        POOL.submit(work).add_done_callback(finished)

    def show_cities(self, cities):
        clear(self.results)
        if not cities and not self.search.get_text().strip():
            self.results.append(label(_('还没有收藏地点，搜索城市后可点击星标收藏。'), 'dim-label'))
        for city in cities:
            button = Gtk.Button()
            button.add_css_class('flat')
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            name = label(city.name, 'heading')
            name.set_xalign(0)
            box.append(name)
            region = label(city.region or city.code, 'dim-label')
            region.set_xalign(0)
            box.append(region)
            row = Gtk.Box(spacing=12)
            box.set_hexpand(True)
            row.append(box)
            selected = Gtk.Image.new_from_icon_name('object-select-symbolic')
            selected.set_visible(bool(self.city and city.code == self.city.code))
            row.append(selected)
            button.set_child(row)
            button.connect('clicked', lambda _, c=city: self.add_city(c))
            self.results.append(button)

    def add_city(self, city):
        # City codes identify locations even when search returns a different label.
        city = next((c for c in self.cities if c.code == city.code), city)
        if city not in self.cities:
            self.cities.append(city)
            storage.save(storage.CONFIG, [asdict(c) for c in self.cities])
        self.select(city)

    def update_location_selector(self):
        self.city_label.set_text(self.city.name if self.city else _('选择地点'))
        self.locations.set_tooltip_text(
            self.city.region or self.city.code if self.city else _('选择地点'))
        if not self.search.get_text().strip():
            self.show_cities(self.cities)

    def search_changed(self, *args):
        self.search_serial += 1
        generation = self.search_serial
        if self.search_timer:
            GLib.source_remove(self.search_timer)
            self.search_timer = None
        query = self.search.get_text().strip()
        if not query:
            self.search_status.set_text(_('收藏城市'))
            self.show_cities(self.cities)
            return
        self.search_status.set_text(_('正在搜索…'))
        clear(self.results)
        def perform():
            self.search_timer = None
            if len(query) == 9 and query.isdigit() and query.startswith('101'):
                self.search_status.set_text(_('按城市代码查询'))
                self.show_cities([provider.City(query, query)])
                return False
            def done(cities, error):
                if generation != self.search_serial:
                    return
                self.search_status.set_text((_('搜索失败：') + error) if error else (_('搜索结果') if cities else _('没有找到城市')))
                self.show_cities(cities or [])
            self.async_call(lambda: provider.search(query), done)
            return False
        self.search_timer = GLib.timeout_add(450, perform)

    def toggle_favorite(self, *_):
        if not self.city:
            return
        if self.city in self.cities:
            self.cities.remove(self.city)
        else:
            self.cities.append(self.city)
        storage.save(storage.CONFIG, [asdict(c) for c in self.cities])
        self.update_star()
        self.update_location_selector()
        if not self.search.get_text():
            self.show_cities(self.cities)

    def update_star(self):
        self.star.set_icon_name('starred-symbolic' if self.city in self.cities else 'non-starred-symbolic')

    def select(self, city):
        self.location_popover.popdown()
        self.window_title.set_title(city.name)
        self.window_title.set_subtitle(_('中国天气'))
        self.city = city
        settings = storage.load(storage.SETTINGS, {})
        if not isinstance(settings, dict):
            settings = {}
        settings['selected_city'] = city.code
        storage.save(storage.SETTINGS, settings)
        self.update_location_selector()
        self.serial += 1
        generation = self.serial
        self.update_star()
        self.refresh.set_sensitive(False)
        cache = storage.CACHE / f'{city.code}.json'
        saved = storage.load(cache, None)
        if not isinstance(saved, dict) or not (saved.get('days') or saved.get('current')) or 'fetched' not in saved or saved.get('city') != asdict(city):
            saved = None
        if saved:
            self.render(saved, _('缓存数据 · 正在更新…'))
        else:
            self.empty(city.name, _('正在获取天气实况和预报…'))
        def work():
            data = dict(city=asdict(city), days=[], fetched=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M'))
            # Independent sources: one failed endpoint must not hide other weather data.
            with ThreadPoolExecutor(max_workers=3) as requests:
                jobs = {requests.submit(fn, city): key for key, fn in
                        [('current', provider.current), ('days', provider.forecast), ('details', provider.details)]}
                for future in as_completed(jobs):
                    key = jobs[future]
                    try:
                        result = future.result()
                        if key == 'details':
                            data.update(result)
                        else:
                            data[key] = result
                    except Exception as error:
                        if key == 'details':
                            data['hourly_error'] = data['observations_error'] = str(error)
                        else:
                            data[key + '_error'] = str(error)
            if not any(data.get(key) for key in ('current', 'days', 'hourly', 'observations')):
                raise ValueError('；'.join(dict.fromkeys(value for key, value in data.items() if key.endswith('_error'))))
            storage.save(cache, data)
            return data
        def done(data, error):
            if generation != self.serial:
                return
            self.refresh.set_sensitive(True)
            if error:
                if saved:
                    self.render(saved, _('更新失败 · 显示缓存天气，请检查网络后重试'))
                else:
                    self.empty(_('暂时无法获取天气'), _('请检查网络后点击刷新。\n') + error)
            else:
                self.render(data, _('部分数据更新失败，请重试') if any(key.endswith('_error') for key in data) else _('已更新'))
        self.async_call(work, done)

    def render(self, data, status):
        clear(self.body)
        current = data.get('current')
        if current:
            overview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, halign=Gtk.Align.CENTER)
            image = Gtk.Image.new_from_icon_name(provider.icon(current['condition']))
            image.set_pixel_size(80)
            overview.append(image)
            summary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            temperature = current.get('temperature')
            summary.append(label(_('温度暂缺') if temperature is None else f'{temperature:g}°', 'temperature'))
            summary.append(label(weather_text(current['condition']), 'title-2'))
            overview.append(summary)
            self.body.append(overview)
            humidity = current.get('humidity')
            aqi = current.get('aqi')
            self.body.append(label(
                (_('湿度 暂缺') if humidity is None else _('湿度 {value:g}%').format(value=humidity)) +
                f"    {weather_text(current['direction'])} {weather_text(current['wind'])}    " +
                (_('AQI 暂缺') if aqi is None else f'AQI {aqi:g} · {_(provider.aqi_description(aqi))}')))
            self.body.append(label(_('实况观测：') + (current.get('updated') or _('时间未提供')) + _(' · 北京时间'), 'dim-label'))
        else:
            self.body.append(label(_('当前实况暂不可用'), 'title-2'))
            self.body.append(label(error_text(data.get('current_error', _('请刷新以获取实时天气'))), 'dim-label'))
        cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        for day in data.get('days', []):
            card = self.weather_card(weather_text(day['date']))
            image = Gtk.Image.new_from_icon_name(provider.icon(day['condition']))
            image.set_pixel_size(48)
            card.append(image)
            card.append(label(weather_text(day['condition'])))
            card.append(label(f"{(day['high'] or '—').replace('℃', '')}°", 'title-1'))
            card.append(label(f"{(day['low'] or '—').replace('℃', '')}°", 'dim-label'))
            card.append(label(weather_text(day['wind']), 'dim-label'))
            cards.append(card)
        daily = self.card_strip(cards) if data.get('days') else label(_('七日预报暂不可用：') + error_text(data.get('days_error', _('请刷新'))))
        self.add_weather_tabs(data, daily)
        self.body.append(label(_('{status} · 获取时间：{time}（北京时间）').format(status=status, time=data['fetched']), 'dim-label'))
        self.body.append(Gtk.LinkButton(uri=f"https://www.weather.com.cn/weather1d/{data['city']['code']}.shtml", label=_('数据来源：中国天气网 ↗')))

    @staticmethod
    def weather_card(title):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, width_request=140)
        card.add_css_class('weather-card')
        card.append(label(title, 'heading'))
        return card

    @staticmethod
    def card_strip(cards):
        # The viewport fills the window; shorter rows sit in its center.
        # Rows wider than the viewport retain their full scrollable width.
        cards.set_halign(Gtk.Align.CENTER)
        return ArrowScroller(cards)

    def add_weather_tabs(self, data, daily):
        stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        # Each tab determines its own height, avoiding empty space from the long observation lists.
        stack.set_vhomogeneous(False)
        previous_tab = self.weather_stack.get_visible_child_name() if self.weather_stack else 'daily'
        self.weather_stack = stack
        self.tab_switcher.set_stack(stack)
        self.header.set_title_widget(self.tab_switcher)
        self.body.append(stack)
        stack.add_titled(daily, 'daily', _('七日预报'))
        hourly = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        stack.add_titled(hourly, 'hourly', _('分时预报'))
        forecast = data.get('hourly', {})
        if forecast.get('rows'):
            hourly.append(label(_('预报发布时间：') + (forecast.get('updated') or _('网站未提供')) + _(' · 北京时间'), 'dim-label'))
            cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            for point in forecast['rows']:
                card = self.weather_card(point['time'])
                image = Gtk.Image.new_from_icon_name(provider.icon(point['condition']))
                image.set_pixel_size(48)
                card.append(image)
                card.append(label(weather_text(point['condition'])))
                card.append(label(point['temperature'], 'title-1'))
                card.append(label(weather_text(point['direction'] + ' ' + point['wind']), 'dim-label'))
                cards.append(card)
            hourly.append(self.card_strip(cards))
        else:
            hourly.append(label(_('分时段预报暂不可用：') + error_text(data.get('hourly_error', _('请刷新以获取数据'))), 'dim-label'))
        observations = data.get('observations', {})
        for field, title, unit in [('temperature', _('温度小时实况'), '℃'),
                                   ('humidity', _('湿度小时实况'), '%'),
                                   ('rain', _('降雨量小时实况'), 'mm'),
                                   ('wind', _('风力小时实况'), _('级'))]:
            page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            tab_title = {'temperature': _('温度'), 'humidity': _('湿度'), 'rain': _('降雨量'), 'wind': _('风力')}[field]
            stack.add_titled(page, field, tab_title)
            page.set_tooltip_text(title)
            points = observations.get('rows', [])
            if not points:
                page.append(label(_('小时实况暂不可用：') + error_text(data.get('observations_error', _('请刷新以获取数据'))), 'dim-label'))
                continue
            page.append(label(_('最近观测：') + observations.get('updated', '—') + _(' · 北京时间'), 'dim-label'))
            page.append(label(title + _('（') + unit + _('） · 时间从早到晚'), 'heading'))
            if any(point.get(field) is not None for point in points):
                page.append(TrendChart(points, field, unit))
            cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            for point in points:
                card = self.weather_card(point['time'])
                value = point.get(field)
                card.append(label(_('缺测') if value is None else f'{value:g} {unit}', 'title-2'))
                if field == 'wind':
                    card.append(label(weather_text(point.get('direction', '') or _('风向暂缺')), 'dim-label'))
                cards.append(card)
            page.append(self.card_strip(cards))

        if previous_tab and stack.get_child_by_name(previous_tab):
            stack.set_visible_child_name(previous_tab)


class Application(Adw.Application):
    def __init__(self):
        settings = storage.load(storage.SETTINGS, {})
        self.language = settings.get('language', 'system') if isinstance(settings, dict) else 'system'
        if self.language not in LANGUAGES:
            self.language = 'system'
        set_language(self.language)
        super().__init__(application_id='io.github.hillwood.ChinaWeather', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        Gtk.Window.set_default_icon_name('io.github.hillwood.ChinaWeather')

        action = Gio.SimpleAction.new_stateful('language', GLib.VariantType.new('s'),
                                              GLib.Variant('s', self.language))
        action.connect('change-state', self.change_language)
        self.add_action(action)

    def change_language(self, action, value):
        language = value.get_string()
        if language not in LANGUAGES or language == self.language:
            return
        settings = storage.load(storage.SETTINGS, {})
        if not isinstance(settings, dict):
            settings = {}
        settings['language'] = language
        storage.save(storage.SETTINGS, settings)
        self.language = language
        action.set_state(value)
        set_language(language)
        old = self.get_active_window()
        tab = old.weather_stack.get_visible_child_name() if old and old.weather_stack else None
        window = Window(self, old.city if old else None)
        if tab and window.weather_stack:
            window.weather_stack.set_visible_child_name(tab)
        window.present()
        if old:
            old.close()

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            # Use the same icon in a source checkout and a system installation.
            source_icons = Path(__file__).resolve().parent.parent / 'data'
            if (source_icons / 'io.github.hillwood.ChinaWeather.svg').is_file():
                Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(str(source_icons))
            css = Gtk.CssProvider()
            css.load_from_data(b'.temperature { font-size: 48px; font-weight: 700; } .weather-card { padding: 20px 12px; border-right: 1px solid alpha(currentColor, 0.12); }')
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            window = Window(self)
        window.present()


def main():
    return Application().run(sys.argv)
