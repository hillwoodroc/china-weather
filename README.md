# China Weather

English | [简体中文](README.zh-CN.md)

A native GNOME weather application inspired by GNOME Weather, built with Python, GTK 4, and libadwaita. It uses public city search and forecast pages from China Weather (中国天气网). No API key is required.

## Running

Install the dependencies on openSUSE Tumbleweed:

```sh
sudo zypper install python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 python3-cairo python3-gobject-cairo gettext-tools
make translations
./china-weather
```

Requires Python 3.10+, GTK 4, and libadwaita 1.0+. You can also run `python3 -m china_weather`.

## Features

- A centered weather overview and forecast tabs inspired by GNOME Weather, with support for the system light and dark themes. Click the city name above the overview to open the search and saved locations popover.
- Search for cities by name or pinyin using the provider's search service. You can also enter a nine-digit Chinese city code, such as `101040100` for Chongqing or `101010100` for Beijing.
- Search and switch between multiple cities in the city dropdown, with a checkmark indicating the current city. Selecting a search result saves the city automatically. The last viewed saved city is restored on startup. Use the star button to remove a city from favorites.
- Current conditions, temperature, relative humidity, wind direction and strength, and AQI, with the observation time. Current observations come from `https://d1.weather.com.cn/sk_2d/{city_code}.html`. Unavailable observations are clearly marked; forecast temperatures are never substituted for current observations.
- Horizontal seven-day forecast cards showing high and low temperatures, conditions, and wind. Hourly forecasts and observation values also use horizontal layouts.
- Adaptive navigation arrows instead of scrollbars. Arrows disappear at the corresponding boundary, and both horizontal arrows disappear when the content fits. Supports smooth paging, mouse wheels, touchpads, and arrow keys. Vertical overflow in shorter windows can be navigated with up and down arrows.
- Six tabs: seven-day forecast, hourly forecast, hourly temperature observations, humidity observations, rainfall observations, and wind observations.
- Trend charts and hourly observation values with timestamps and units. Hourly forecasts include their publication time.
- Observations appear in chronological order, retaining dates across midnight. Zero values are preserved, missing values are labeled, and charts show gaps for missing data.
- Hourly forecasts and observations are extracted from the daily weather page's `hour3data` and `observe24h_data` fields. Only JSON is decoded; scripts are never executed. Errors in these sources are handled independently so that available seven-day forecasts remain visible.
- Starred favorites, manual refresh, and automatic refresh every 30 minutes.
- Background network requests, debounced search, and protection against outdated responses, keeping the window responsive.
- Cached weather with its retrieval time when network updates fail. If no cache is available, an error message and refresh control are provided.
- A link at the bottom of the page opens the corresponding city page on China Weather.

Favorites are stored in `$XDG_CONFIG_HOME/china-weather/cities.json`, and cached weather is stored in `$XDG_CACHE_HOME/china-weather/`. If these environment variables are unset, the application uses `~/.config` and `~/.cache`, respectively.

## Installation

```sh
make install PREFIX="$HOME/.local"
```
