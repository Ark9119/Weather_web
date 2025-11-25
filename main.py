from typing import Dict, Any
import uvicorn
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from response_transformation import (
    format_weather_for_today,
    format_weather_for_now,
    format_weather_for_days
)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
# Инициализация шаблонизатора
templates = Jinja2Templates(directory="templates")

# Базовые настройки
WEATHER_API_BASE_URL = "http://127.0.0.1:8000/weather"
AUTH_API_URL = "http://127.0.0.1:8000/city/"
DEFAULT_CITY = "санкт-петербург"
DEFAULT_DAYS = 1

# Конфигурация эндпоинтов
WEATHER_ENDPOINTS = {
    "now": {
        "url": "/now/",
        "template": "includes/weather_now.html",
        "title": "Текущая погода"
    },
    "today": {
        "url": "/today/",
        "template": "includes/weather_today.html",
        "title": "Погода на сегодня"
    },
    "weather_to_days": {
        "url": "/weather_to_days/",
        "template": "includes/weather_to_days.html",
        "title": "Прогноз погоды"
    }
}


def create_user_identifier(name: str, password: str) -> str:
    """Создание уникального идентификатора пользователя"""
    return f'@{name}@@{password}@'


def parse_user_identifier(user_identifier: str) -> Dict[str, str]:
    """Парсинг идентификатора пользователя"""
    try:
        # Убираем начальный и конечный @
        cleaned = user_identifier[1:-1]
        parts = cleaned.split("@@")
        return {
            "name": parts[0],
            "password": parts[1],
        }
    except Exception:
        return {}


async def get_user_city(user_identifier: str) -> str:
    """Получение города пользователя из API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTH_API_URL}{user_identifier}/")
            if response.status_code == 200:
                data = response.json()
                return data.get("city", DEFAULT_CITY)
    except Exception:
        pass
    return DEFAULT_CITY


async def fetch_weather_data(
    endpoint: str,
    city: str,
    days: int
) -> Dict[str, Any]:
    """
    Общая функция для получения данных о погоде из API
    """
    if endpoint not in WEATHER_ENDPOINTS:
        raise ValueError(f"Неизвестный эндпоинт: {endpoint}")
    api_url = WEATHER_API_BASE_URL + WEATHER_ENDPOINTS[endpoint]["url"]
    payload = {"city": city, "days": days}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        # Парсим ответ независимо от статуса
        response_data = response.json()
        # Если статус не успешный, проверяем наличие ошибки в ответе
        if response.status_code != 200:
            error_message = response_data.get("error", "Неизвестная ошибка")
            # Возвращаем словарь с ошибкой вместо вызова исключения
            return {"error": error_message}
        return response_data


async def render_weather_template(
    request: Request,
    endpoint: str,
    city: str | None = None,
    days: int = DEFAULT_DAYS
):
    """
    Общая функция для рендеринга шаблонов погоды
    """
    # всегда используем город пользователя, если он авторизован
    if endpoint == 'weather_to_days':
        days = 3
    elif endpoint == 'today' or endpoint == 'now':
        days = DEFAULT_DAYS
    user_identifier = request.cookies.get("user_identifier")
    if user_identifier:
        # Для авторизованного пользователя всегда используем город из базы
        actual_city = await get_user_city(user_identifier)
    else:
        # Для неавторизованного используем переданный
        # город или город по умолчанию
        actual_city = city or DEFAULT_CITY
    try:
        weather_data = await fetch_weather_data(endpoint, actual_city, days)
        # Проверяем, вернулась ли ошибка из API
        if "error" in weather_data:
            return templates.TemplateResponse(
                WEATHER_ENDPOINTS[endpoint]["template"],
                {
                    "request": request,
                    "error": weather_data["error"],
                    "title": WEATHER_ENDPOINTS[endpoint]["title"],
                    "city": actual_city,
                    "days": days
                }
            )
        # Форматирование данных в зависимости от эндпоинта
        formatted_data = []
        if endpoint == "now":
            formatted_day = format_weather_for_now(
                    actual_city, weather_data['forecast'][0]
                )
            formatted_data = [formatted_day]
        elif endpoint == "today":
            formatted_day = format_weather_for_today(
                    actual_city, weather_data['forecast'][0]
                )
            formatted_data = [formatted_day]
        elif endpoint == "weather_to_days":
            formatted_data = format_weather_for_days(
                    actual_city, weather_data['forecast']
                )
        return templates.TemplateResponse(
            WEATHER_ENDPOINTS[endpoint]["template"],
            {
                "request": request,
                "weather_data": formatted_data,
                "title": WEATHER_ENDPOINTS[endpoint]["title"],
                "city": actual_city,
                "days": days
            }
        )
    except httpx.ConnectError:
        return templates.TemplateResponse(
            WEATHER_ENDPOINTS[endpoint]["template"],
            {
                "request": request,
                "error": "Не удалось подключиться к сервису погоды",
                "title": WEATHER_ENDPOINTS[endpoint]["title"],
                "city": actual_city,
                "days": days
            }
        )
    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            error_message = error_data.get("error", "Неизвестная ошибка API")
        except Exception:
            error_message = "Ошибка при обработке ответа от сервиса погоды"
        return templates.TemplateResponse(
            WEATHER_ENDPOINTS[endpoint]["template"],
            {
                "request": request,
                "error": error_message,
                "title": WEATHER_ENDPOINTS[endpoint]["title"],
                "city": actual_city,
                "days": days
            }
        )
    except Exception:
        return templates.TemplateResponse(
            WEATHER_ENDPOINTS[endpoint]["template"],
            {
                "request": request,
                "error": "Произошла внутренняя ошибка сервера",
                "title": WEATHER_ENDPOINTS[endpoint]["title"],
                "city": actual_city,
                "days": days
            }
        )


@app.get("/weather/now")
async def weather_now(
    request: Request, city: str | None = None, days: int = DEFAULT_DAYS
):
    """
    Эндпоинт для получения текущей погоды
    """
    return await render_weather_template(request, "now", city, days)


@app.get("/weather/today")
async def weather_today(
    request: Request, city: str | None = None, days: int = DEFAULT_DAYS
):
    """
    Эндпоинт для получения погоды на сегодня
    """
    return await render_weather_template(request, "today", city, days)


@app.get("/weather/weather_to_days")
async def weather_to_days(
    request: Request, city: str | None = None, days: int = DEFAULT_DAYS
):
    """
    Эндпоинт для получения прогноза погоды на несколько дней
    """
    return await render_weather_template(
        request, "weather_to_days", city, days
    )


@app.get("/register")
def register_form(request: Request):
    """Форма регистрации"""
    return templates.TemplateResponse(
        "includes/register.html", {"request": request}
    )


@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    city: str = Form(...),
    password: str = Form(...)
):
    """Обработка регистрации"""
    try:
        user_identifier = create_user_identifier(name, password)
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                AUTH_API_URL,
                json={
                    "city": city,
                    "user": user_identifier
                },
                headers={"Content-Type": "application/json"}
            )
            if auth_response.status_code == 200:
                response = RedirectResponse(url="/", status_code=303)
                response.set_cookie(
                    key="user_identifier",
                    value=user_identifier,
                    httponly=True,
                    max_age=3600
                )
                return response
            else:
                error_data = auth_response.json()
                error_message = error_data.get("error", "Ошибка регистрации")
                return templates.TemplateResponse(
                    "includes/register.html",
                    {
                        "request": request,
                        "error": error_message
                    }
                )
    except Exception as e:
        return templates.TemplateResponse(
            "includes/register.html",
            {
                "request": request,
                "error": f"Ошибка при регистрации: {str(e)}"
            }
        )


@app.get("/login")
def login_form(request: Request):
    """Форма входа"""
    return templates.TemplateResponse(
        "includes/login.html", {"request": request}
    )


@app.post("/login")
async def login(
    request: Request,
    name: str = Form(...),
    password: str = Form(...)
):
    """Обработка входа"""
    try:
        user_identifier = create_user_identifier(name, password)
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                f"{AUTH_API_URL}{user_identifier}/"
            )
            if auth_response.status_code == 200:
                response = RedirectResponse(url="/", status_code=303)
                response.set_cookie(
                    key="user_identifier",
                    value=user_identifier,
                    httponly=True,
                    max_age=3600
                )
                return response
            else:
                return templates.TemplateResponse(
                    "includes/login.html",
                    {
                        "request": request,
                        "error": "Неверное имя пользователя или пароль"
                    }
                )
    except Exception as e:
        return templates.TemplateResponse(
            "includes/login.html",
            {
                "request": request,
                "error": f"Ошибка при входе: {str(e)}"
            }
        )


@app.post("/update_city")
async def update_city(
    request: Request,
    city: str = Form(...)
):
    """Обновление города пользователя"""
    try:
        user_identifier = request.cookies.get("user_identifier")
        if not user_identifier:
            return RedirectResponse(url="/login", status_code=303)
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                AUTH_API_URL,
                json={
                    "city": city,
                    "user": user_identifier
                },
                headers={"Content-Type": "application/json"}
            )
            if auth_response.status_code == 200:
                return RedirectResponse(url="/", status_code=303)
            else:
                return RedirectResponse(url="/", status_code=303)
    except Exception:
        return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user_identifier")
    return response


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        'includes/index.html',
        {"request": request}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
