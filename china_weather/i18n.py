"""Gettext translations, with weather data localized only at display time."""
import gettext
import os
from pathlib import Path
import re

DOMAIN = 'china-weather'
LOCALEDIR = Path(__file__).resolve().parent / 'locale'
LANGUAGES = {'system': 'System / 系统 / 系統', 'zh_CN': '简体中文',
             'zh_TW': '繁體中文', 'en': 'English'}


def system_language(environ=None):
    env = os.environ if environ is None else environ
    locale = env.get('LC_ALL') or env.get('LC_MESSAGES') or env.get('LANG') or 'en'
    if locale in ('C', 'POSIX', 'C.UTF-8', 'C.utf8'):
        return 'en'
    candidates = env.get('LANGUAGE', '').split(':') + [locale]
    for candidate in candidates:
        code = candidate.lower().replace('-', '_')
        if code.startswith('zh'):
            return 'zh_TW' if any(part in code for part in ('tw', 'hk', 'mo', 'hant')) else 'zh_CN'
        if code.startswith('en'):
            return 'en'
    return 'en'


_language = system_language()
_translation = gettext.translation(DOMAIN, localedir=LOCALEDIR,
                                   languages=[_language], fallback=True)


def set_language(language):
    global _language, _translation
    _language = system_language() if language == 'system' else language if language in LANGUAGES else system_language()
    _translation = gettext.translation(DOMAIN, localedir=LOCALEDIR,
                                       languages=[_language], fallback=True)


def translate(message):
    return _translation.gettext(message)


def N_(message):
    """Mark messages that arrive from the provider for extraction."""
    return message


def weather_message(context, message):
    """Mark weather tokens for extraction; translate them at display time."""
    return message


MESSAGES = (
    N_('网站'),
    N_('开发版'),
    N_('主菜单'),
    N_('温度单位'),
    N_('摄氏度 (°C)'),
    N_('华氏度 (°F)'),
    N_('关于中国天气'),
    N_('查看中国城市的实时天气与预报。'),
    N_('项目主页'),

    N_('中国天气'),
    N_('刷新天气'),
    N_('收藏或取消收藏城市'),
    N_('选择地点'),
    N_('搜索城市 / 拼音'),
    N_('收藏城市'),
    N_('查看你关心的天气'),
    N_('选择地点，查看当地天气和预报。'),
    N_('还没有收藏地点，搜索城市后可点击星标收藏。'),
    N_('正在搜索…'),
    N_('按城市代码查询'),
    N_('搜索失败：'),
    N_('搜索结果'),
    N_('没有找到城市'),
    N_('缓存数据 · 正在更新…'),
    N_('正在获取天气实况和预报…'),
    N_('更新失败 · 显示缓存天气，请检查网络后重试'),
    N_('暂时无法获取天气'),
    N_('请检查网络后点击刷新。\n'),
    N_('部分数据更新失败，请重试'),
    N_('已更新'),
    N_('温度暂缺'),
    N_('湿度 暂缺'),
    N_('AQI 暂缺'),
    N_('实况观测：'),
    N_('时间未提供'),
    N_(' · 北京时间'),
    N_('当前实况暂不可用'),
    N_('请刷新以获取实时天气'),
    N_('七日预报暂不可用：'),
    N_('请刷新'),
    N_('数据来源：中国天气网 ↗'),
    N_('七日预报'),
    N_('分时预报'),
    N_('预报发布时间：'),
    N_('网站未提供'),
    N_('分时段预报暂不可用：'),
    N_('请刷新以获取数据'),
    N_('温度小时实况'),
    N_('湿度小时实况'),
    N_('降雨量小时实况'),
    N_('风力小时实况'),
    N_('级'),
    N_('温度'),
    N_('湿度'),
    N_('降雨量'),
    N_('风力'),
    N_('小时实况暂不可用：'),
    N_('最近观测：'),
    N_('（'),
    N_('） · 时间从早到晚'),
    N_('缺测'),
    N_('风向暂缺'),
    N_('向上滚动'),
    N_('向下滚动'),
    N_('向左滚动'),
    N_('向右滚动'),
    N_('时间从左到右排列；具体数值见下方列表。断点表示缺测。'),
    N_('未找到七日预报，网站结构可能已更新'),
    N_('天气页面没有可用预报'),
    N_('城市搜索返回格式已变化'),
    N_('搜索服务返回了记录，但未能识别国内城市数据'),
    N_('无效的城市代码'),
    N_('页面没有可用的分时段预报'),
    N_('页面没有可用的小时实况'),
    N_('未找到当前天气实况'),
    N_('当前天气实况格式已变化'),
    N_('实况返回的城市代码不匹配'),
    N_('天气现象暂缺'),
    N_('风力暂缺'),
    N_('暂无数据'),
    N_('优'),
    N_('良'),
    N_('轻度污染'),
    N_('中度污染'),
    N_('重度污染'),
    N_('严重污染'),
    N_('湿度 {value:g}%'),
    N_('{status} · 获取时间：{time}（北京时间）'),
    N_('页面没有提供 {name} 数据'),
    N_('语言'),
    N_('跟随系统'),
)

WEATHER = (
    weather_message('weather', '晴'),
    weather_message('weather', '多云'),
    weather_message('weather', '阴'),
    weather_message('weather', '雷阵雨'),
    weather_message('weather', '阵雨'),
    weather_message('weather', '雨夹雪'),
    weather_message('weather', '雷阵雨伴有冰雹'),
    weather_message('weather', '特大暴雨'),
    weather_message('weather', '大暴雨'),
    weather_message('weather', '暴雨'),
    weather_message('weather', '大雨'),
    weather_message('weather', '中雨'),
    weather_message('weather', '小雨'),
    weather_message('weather', '暴雪'),
    weather_message('weather', '大雪'),
    weather_message('weather', '中雪'),
    weather_message('weather', '小雪'),
    weather_message('weather', '阵雪'),
    weather_message('weather', '浮尘'),
    weather_message('weather', '扬沙'),
    weather_message('weather', '强沙尘暴'),
    weather_message('weather', '沙尘暴'),
    weather_message('weather', '雾'),
    weather_message('weather', '霾'),
    weather_message('weather', '东北风'),
    weather_message('weather', '东南风'),
    weather_message('weather', '西北风'),
    weather_message('weather', '西南风'),
    weather_message('weather', '东风'),
    weather_message('weather', '南风'),
    weather_message('weather', '西风'),
    weather_message('weather', '北风'),
    weather_message('weather', '无持续风向'),
    weather_message('weather', '微风'),
    weather_message('weather', '今天'),
    weather_message('weather', '明天'),
    weather_message('weather', '后天'),
    weather_message('weather', '星期'),
    weather_message('weather', '周一'),
    weather_message('weather', '周二'),
    weather_message('weather', '周三'),
    weather_message('weather', '周四'),
    weather_message('weather', '周五'),
    weather_message('weather', '周六'),
    weather_message('weather', '周日'),
    weather_message('weather', '转'),
    weather_message('weather', '到'),
    weather_message('weather', '级'),
    weather_message('weather', '日'),
    weather_message('weather', '小于'),
)


def weather_text(text):
    """Never mutate provider values or cached data."""
    text = str(text)
    if text in MESSAGES:
        return translate(text)
    pattern = '|'.join(re.escape(key) for key in sorted(WEATHER, key=len, reverse=True))
    return re.sub(pattern, lambda match: _translation.pgettext('weather', match[0]), text)


def error_text(text):
    text = str(text)
    for message in sorted(MESSAGES, key=len, reverse=True):
        if message in text:
            text = text.replace(message, translate(message))
    return re.sub(r'页面没有提供 (\w+) 数据',
                  lambda match: translate('页面没有提供 {name} 数据').format(name=match[1]), text)
