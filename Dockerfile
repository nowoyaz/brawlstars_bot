FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Убираем создание /app/data внутри контейнера, так как она будет монтироваться снаружи
RUN mkdir -p /data && chown -R 32767:32767 /data && chmod -R 777 /data

# Копируем только requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем всё приложение
COPY . .

CMD ["python", "main.py"]
