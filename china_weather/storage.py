import json
import os
from pathlib import Path


def load(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'china-weather' / 'cities.json'
CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'china-weather'

SETTINGS = CONFIG.with_name('settings.json')
