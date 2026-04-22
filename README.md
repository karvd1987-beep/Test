# Review Radar MVP (Python WebApp)

MVP-сервис для мониторинга и анализа отзывов с фокусом на Яндекс Карты.

## Что реализовано в этом инкременте

- FastAPI backend + webapp (Jinja templates).
- Анонимный демо-анализ по ссылке на Яндекс Карты.
- Регистрация пользователя и запуск trial (7 дней, 1 ссылка).
- Подключение точек в личном кабинете (после оплаты до 5 ссылок).
- Мониторинг отзывов (MVP-адаптер источника + детект новых отзывов).
- AI-модуль (изолированный интерфейс + базовая эвристика критичности).
- Каналы уведомлений через абстракции (Email / Telegram / MAX).
- Черновой финальный отчёт по trial.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Откройте `http://127.0.0.1:8000`.

## Архитектура

Проект организован как modular monolith:

- `app/domain` — сущности и контракты.
- `app/services` — use-case логика.
- `app/infrastructure` — реализации адаптеров/репозиториев.
- `app/web` — API, схемы, web handlers.
- `app/templates` — HTML шаблоны webapp.