from typing import Dict, List
from datetime import datetime


def weather_emoji_status(rain_chance: int, cloud: int) -> tuple[str, str]:
    """Определение состояния погоды для эмодзи"""
    if rain_chance > 50:
        weather_emoji = '🌧️'
        weather_status = 'Дождь'
    elif cloud > 70:
        weather_emoji = '☁️'
        weather_status = 'Облачно'
    elif cloud > 30:
        weather_emoji = '⛅'
        weather_status = 'Переменная облачность'
    else:
        weather_emoji = '☀️'
        weather_status = 'Ясно'
    return weather_emoji, weather_status


def format_weather_for_days(
    city: str, forecast_data: List[Dict]
) -> List[Dict]:
    """Форматирование данных для прогноза на несколько дней"""
    formatted_days = []
    for forecast in forecast_data:
        user_city = city
        found_country = forecast['found_country']
        found_city = forecast['found_city']
        date = forecast['date']
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d.%m.%Y')
        min_temp_c = min(forecast['temp_c'])
        max_temp_c = max(forecast['temp_c'])
        avg_temp = sum(forecast['temp_c']) / len(forecast['temp_c'])
        clouds = forecast['cloud']
        humidity = forecast['humidity']
        rain_chance = forecast['chance_of_rain']
        avg_cloud = sum(clouds) / len(clouds)
        avg_humidity = sum(humidity) / len(humidity)
        max_rain_chance = max(rain_chance)
        weather_emoji, weather_status = weather_emoji_status(
            max_rain_chance, avg_cloud
        )
        formatted_day = {
            'user_city': user_city,
            'found_country': found_country,
            'found_city': found_city,
            'date': formatted_date,
            'min_temp': f'{min_temp_c:.1f}',
            'max_temp': f'{max_temp_c:.1f}',
            'avg_temp': f'{avg_temp:.1f}',
            'avg_cloud': f'{avg_cloud:.0f}',
            'avg_humidity': f'{avg_humidity:.0f}',
            'max_rain_chance': f'{max_rain_chance:.0f}',
            'weather_emoji': weather_emoji,
            'weather_status': weather_status
        }
        formatted_days.append(formatted_day)
    return formatted_days


def format_weather_for_now(city: str, forecast_data: Dict) -> Dict:
    """Форматирование данных для текущей погоды"""
    user_city = city
    found_country = forecast_data['found_country']
    found_city = forecast_data['found_city']
    date = forecast_data['date']
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%d.%m.%Y')
    # Для текущей погоды берем первый элемент (текущий час)
    temp_c = forecast_data['temp_c']
    cloud = forecast_data['cloud']
    humidity = forecast_data['humidity']
    rain_chance = forecast_data['chance_of_rain']
    weather_emoji, weather_status = weather_emoji_status(rain_chance, cloud)
    return {
        'user_city': user_city,
        'found_country': found_country,
        'found_city': found_city,
        'date': formatted_date,
        'temp_c': f'{temp_c:.1f}',
        'cloud': f'{cloud:.0f}',
        'humidity': f'{humidity:.0f}',
        'rain_chance': f'{rain_chance:.0f}',
        'weather_emoji': weather_emoji,
        'weather_status': weather_status
    }


def format_weather_for_today(city: str, forecast_data: Dict) -> Dict:
    """Форматирование данных для погоды на сегодня"""
    user_city = city
    found_country = forecast_data['found_country']
    found_city = forecast_data['found_city']
    date = forecast_data['date']
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%d.%m.%Y')
    # Для сегодняшнего дня вычисляем статистику
    min_temp_c = min(forecast_data['temp_c'])
    max_temp_c = max(forecast_data['temp_c'])
    avg_temp = sum(forecast_data['temp_c']) / len(forecast_data['temp_c'])
    clouds = forecast_data['cloud']
    humidity = forecast_data['humidity']
    rain_chance = forecast_data['chance_of_rain']
    avg_cloud = sum(clouds) / len(clouds)
    avg_humidity = sum(humidity) / len(humidity)
    max_rain_chance = max(rain_chance)
    weather_emoji, weather_status = weather_emoji_status(
        max_rain_chance, avg_cloud
    )
    return {
        'user_city': user_city,
        'found_country': found_country,
        'found_city': found_city,
        'date': formatted_date,
        'min_temp': f'{min_temp_c:.1f}',
        'max_temp': f'{max_temp_c:.1f}',
        'avg_temp': f'{avg_temp:.1f}',
        'avg_cloud': f'{avg_cloud:.0f}',
        'avg_humidity': f'{avg_humidity:.0f}',
        'max_rain_chance': f'{max_rain_chance:.0f}',
        'weather_emoji': weather_emoji,
        'weather_status': weather_status
    }
