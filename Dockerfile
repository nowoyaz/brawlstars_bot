FROM python:3.11-slim

WORKDIR /app

# Убираем создание /app/data внутри контейнера, так как она будет монтироваться снаружи
RUN mkdir -p /data && chown -R 32767:32767 /data && chmod -R 777 /data

# Копируем только requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем всё приложение
COPY . .

CMD ["python", "main.py"]
