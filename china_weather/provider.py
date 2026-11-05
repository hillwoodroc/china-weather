"""China Weather HTML/JSONP adapter. No third-party Python dependencies."""
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class City:
    code: str
    name: str
    region: str = ''


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    @property
    def text(self):
        return ''.join(c.text if isinstance(c, Node) else c for c in self.children).strip()

    def find(self, tag=None, cls=None):
        result = []
        for child in self.children:
            if isinstance(child, Node):
                if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get('class', '').split()):
                    result.append(child)
                result.extend(child.find(tag, cls))
        return result


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'input', 'img', 'br', 'hr', 'meta', 'link', 'source', 'wbr', 'area', 'embed', 'param', 'track', 'col', 'base'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_forecast(html):
    root = Document(html).root
    containers = [n for n in root.find() if n.attrs.get('id') == '7d']
    if not containers:
        raise ValueError('未找到七日预报，网站结构可能已更新')
    days = []
    for li in containers[0].find('li'):
        dates, conditions, temps = li.find('h1'), li.find(cls='wea'), li.find(cls='tem')
        if not (dates and conditions and temps):
            continue
        highs, lows = temps[0].find('span'), temps[0].find('i')
        wind = li.find(cls='win')
        days.append(dict(date=dates[0].text, condition=conditions[0].text,
                         high=highs[0].text if highs else None,
                         low=lows[0].text if lows else None,
                         wind=wind[0].text if wind else ''))
    if not days:
        raise ValueError('天气页面没有可用预报')
    return days[:7]


def parse_search(payload):
    # The endpoint wraps its array in JavaScript; never evaluate the response.
    start, end = payload.find('['), payload.rfind(']')
    if start < 0 or end < start:
        raise ValueError('城市搜索返回格式已变化')
    rows = json.loads(payload[start:end + 1])
    if not isinstance(rows, list):
        raise ValueError('城市搜索返回格式已变化')
    cities, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        ref = row.get('ref', '')
        if isinstance(ref, str) and ref.lstrip().startswith('{'):
            try:
                ref = json.loads(ref)
            except ValueError:
                pass
        details = dict(row)
        if isinstance(ref, dict):
            details.update(ref)
        parts = ref.split('~') if isinstance(ref, str) else []
        candidates = [details.get(key, '') for key in ('id', 'code', 'cityCode', 'citycode')] + parts
        code = next((str(value).strip() for value in candidates
                     if re.fullmatch(r'101\d{6}', str(value).strip())), None)
        if not code or code in seen:
            continue
        name = next((details[key] for key in ('cityName', 'cityname', 'name', 'c1', 'c2')
                     if details.get(key)), None)
        if not name:
            name = next((part for part in parts if re.search(r'[\u3400-\u9fff]', part)), None)
        if not name:
            continue
        region = ' · '.join(dict.fromkeys(str(details[k]) for k in ('c7', 'c5', 'c2')
                                         if details.get(k) and details[k] != name))
        cities.append(City(code, str(name), region))
        seen.add(code)
    if rows and not cities:
        raise ValueError('搜索服务返回了记录，但未能识别国内城市数据')
    return cities


def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (ChinaWeather desktop)',
                               'Referer': 'https://www.weather.com.cn/'})
    with urlopen(req, timeout=15) as response:
        return response.read(2_000_000).decode('utf-8-sig')


def search(query):
    return parse_search(fetch('https://toy1.weather.com.cn/search?' + urlencode({'cityname': query.strip(), 'callback': 'success_jsonpCallback'})))


def forecast(city):
    if not re.fullmatch(r'101\d{6}', city.code):
        raise ValueError('无效的城市代码')
    return parse_forecast(fetch(f'https://www.weather.com.cn/weather/{city.code}.shtml'))


def icon(condition):
    for word, name in [('雷', 'weather-storm-symbolic'), ('雪', 'weather-snow-symbolic'),
                       ('雨', 'weather-showers-symbolic'), ('雾', 'weather-fog-symbolic'),
                       ('霾', 'weather-fog-symbolic'), ('阴', 'weather-overcast-symbolic'),
                       ('云', 'weather-few-clouds-symbolic')]:
        if word in condition:
            return name
    return 'weather-clear-symbolic'


def script_json(html, name):
    """Decode a named JSON assignment inside scripts, without executing JavaScript."""
    for script in Document(html).root.find('script'):
        match = re.search(r'\b(?:var\s+|let\s+|const\s+)?' + re.escape(name) + r'\s*=\s*', script.text)
        if match:
            value, _ = json.JSONDecoder().raw_decode(script.text[match.end():])
            return value
    raise ValueError(f'页面没有提供 {name} 数据')


def parse_hourly(html):
    raw = script_json(html, 'hour3data')
    result = []
    for entry in raw.get('1d', []):
        if not isinstance(entry, str):
            continue
        parts = entry.split(',')
        if len(parts) >= 6:
            result.append(dict(time=parts[0], condition=parts[2], temperature=parts[3],
                               direction=parts[4], wind=parts[5]))
    if not result:
        raise ValueError('页面没有可用的分时段预报')
    root = Document(html).root
    updated = next((node.attrs.get('value', '') for node in root.find('input')
                    if node.attrs.get('id') == 'fc_3h_internal_update_time'), '')
    return dict(updated=updated, rows=result)


def observation_value(value):
    import math
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    # Website uses empty strings and 9999-style sentinels for missing observations.
    return number if math.isfinite(number) and abs(number) < 999 else None


def parse_observations(html):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    raw = script_json(html, 'observe24h_data')['od']
    latest = datetime.strptime(raw['od0'], '%Y%m%d%H%M').replace(tzinfo=ZoneInfo('Asia/Shanghai'))
    previous = None
    result = []
    for entry in raw.get('od2', []):
        try:
            hour = int(entry['od21'])
            instant = (previous or latest).replace(hour=hour, minute=0)
            if instant > latest or (previous is not None and instant >= previous):
                instant -= timedelta(days=1)
        except (ValueError, KeyError, TypeError):
            continue
        previous = instant
        result.append(dict(time=instant.strftime('%m-%d %H:%M'),
                           temperature=observation_value(entry.get('od22')),
                           humidity=observation_value(entry.get('od27')),
                           rain=observation_value(entry.get('od26')),
                           wind=observation_value(entry.get('od25')),
                           direction=entry.get('od24', '')))
    if not result:
        raise ValueError('页面没有可用的小时实况')
    return dict(updated=latest.strftime('%Y-%m-%d %H:%M'), rows=list(reversed(result)))


def details(city):
    if not re.fullmatch(r'101\d{6}', city.code):
        raise ValueError('无效的城市代码')
    html = fetch(f'https://www.weather.com.cn/weather1d/{city.code}.shtml')
    result = {}
    for key, parser in [('hourly', parse_hourly), ('observations', parse_observations)]:
        try:
            result[key] = parser(html)
        except (ValueError, KeyError, TypeError) as error:
            result[key + '_error'] = str(error)
    return result


def parse_current(payload):
    """Read the site's current observation, never substituting forecast values."""
    match = re.search(r'\b(?:var\s+)?dataSK\s*=\s*', payload)
    if not match:
        raise ValueError('未找到当前天气实况')
    raw, _ = json.JSONDecoder().raw_decode(payload[match.end():])
    if not isinstance(raw, dict) or not raw.get('city'):
        raise ValueError('当前天气实况格式已变化')
    return dict(city=str(raw['city']), condition=raw.get('weather') or '天气现象暂缺',
                temperature=observation_value(raw.get('temp')),
                humidity=observation_value(str(raw.get('SD', raw.get('sd', ''))).rstrip('%')),
                direction=raw.get('WD') or '风向暂缺', wind=raw.get('WS') or '风力暂缺',
                aqi=observation_value(raw.get('aqi')),
                updated=' '.join(str(raw.get(key) or '') for key in ('date', 'time')).strip())


def current(city):
    if not re.fullmatch(r'101\d{6}', city.code):
        raise ValueError('无效的城市代码')
    result = parse_current(fetch(f'https://d1.weather.com.cn/sk_2d/{city.code}.html'))
    if result['city'] != city.code:
        raise ValueError('实况返回的城市代码不匹配')
    return result


def aqi_description(value):
    if value is None or value < 0:
        return '暂无数据'
    for ceiling, text in [(50, '优'), (100, '良'), (150, '轻度污染'),
                          (200, '中度污染'), (300, '重度污染')]:
        if value <= ceiling:
            return text
    return '严重污染'
