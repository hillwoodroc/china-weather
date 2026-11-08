"""Convert temperatures for display without changing cached Celsius data."""
import math


def convert_temperature(value, unit='celsius'):
    if isinstance(value, str):
        value = value.strip().removesuffix('℃').removesuffix('°C').removesuffix('°').strip()
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number * 9 / 5 + 32 if unit == 'fahrenheit' else number


def format_temperature(value, unit='celsius'):
    number = convert_temperature(value, unit)
    symbol = '°F' if unit == 'fahrenheit' else '°C'
    return '—' if number is None else f'{number:g}{symbol}'
