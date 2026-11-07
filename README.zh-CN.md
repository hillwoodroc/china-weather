# 中国天气

[English](README.md) | 简体中文

参考 GNOME Weather 信息布局的原生 GNOME 天气应用，使用 Python、GTK 4 和 libadwaita。数据来源为中国天气网的公开城市搜索和七日预报页面，不需要 API 密钥。

## 运行

openSUSE Tumbleweed 安装依赖：

```sh
sudo zypper install python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 python3-cairo python3-gobject-cairo gettext-tools
make translations
./china-weather
```

需要 Python 3.10+、GTK 4、libadwaita 1.0+。也可以使用 `python3 -m china_weather`。

## 功能

- 以 GNOME Weather 风格显示居中的天气概览与预报标签页，支持系统深浅色主题。点击天气概览上方的城市名称打开搜索和收藏弹出面板，无常驻侧边栏。
- 城市名称 / 拼音搜索（依赖网站搜索服务）；也可输入九位国内城市代码，例如重庆 `101040100`、北京 `101010100`。
- 城市名称下拉弹窗支持搜索和切换多个城市，勾号标出当前城市；选中搜索结果后自动保存城市，重启后恢复上次查看的收藏城市。可用星标取消收藏。
- 主天气区显示当前天气、温度、相对湿度、风向风力和 AQI，标注实况观测时间。当前实况来自 `https://d1.weather.com.cn/sk_2d/{城市代码}.html`；不可用时明确提示，不使用预报温度替代。
- 七日预报按横向卡片显示最高温、最低温、天气及风力。分时预报及小时实况数值也采用横向排列。
- 内容区域使用自适应导航箭头，不显示滚动条；到达边界时隐藏对应方向的箭头，窗口足够宽时隐藏两侧箭头。支持平滑翻页、鼠标滚轮、触控板及方向键；矮窗口的纵向溢出也可用上下箭头浏览。
- 六个标签页：七日预报、分时段预报、温度小时实况、湿度小时实况、降雨量小时实况、风力小时实况。
- 小时实况提供趋势图和逐时数值，标注观测时间及单位；分时段预报标注发布时间。
- 实况按时间从早到晚排列，跨午夜保留日期；零值正常显示，缺测显示为“缺测”，图表保留断点。
- 分时段预报和实况从今日天气页面的 `hour3data`、`observe24h_data` 提取，只解码 JSON，不执行脚本。新增部分单独处理错误，不影响已取得的七日预报。
- 星标收藏、手动刷新、每 30 分钟自动刷新。
- 后台网络请求、搜索防抖及过期响应隔离，不阻塞窗口。
- 网络失败时显示带获取时间的缓存，没有缓存时显示错误和刷新入口。
- 页底可以直接打开对应的中国天气网页面。

收藏保存在 `$XDG_CONFIG_HOME/china-weather/cities.json`，缓存保存在 `$XDG_CACHE_HOME/china-weather/`；未设置时遵循 `~/.config` 和 `~/.cache`。

## 安装

```sh
make install PREFIX="$HOME/.local"
```
