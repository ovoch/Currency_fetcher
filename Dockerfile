# 1. Берем официальный образ Python (например, 3.12, облегченная версия slim)
FROM python:3.12-slim

ENV POETRY_REQUESTS_TIMEOUT=300
ENV POETRY_HTTP_TIMEOUT=300
# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 3. Ставим системные пакеты и сам Poetry
RUN pip install poetry

# 4. Чтобы Poetry не создавал виртуальные окружения внутри Docker 
# (ведь Docker сам по себе - изолированная среда!), мы меняем его настройки:
RUN poetry config virtualenvs.create false

# 5. Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# 6. Устанавливаем библиотеки (fastapi, sqlalchemy и т.д.) без установки самого проекта
RUN poetry install --no-root

# 7. Копируем ВЕСЬ НАШ ИСХОДНЫЙ КОД в папку /app
COPY . .

# 8. Команда для запуска нашего сервера
# Вспомни, как мы запускали uvicorn из консоли? 
# Но теперь мы пишем ее без "python -m poetry run", потому что зависимости установлены глобально в контейнере!
# Плюс нужно указать хост 0.0.0.0, чтобы сервер смотрел наружу контейнера.

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]