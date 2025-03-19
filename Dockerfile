FROM python:3.11-slim

WORKDIR /app

# Создаем директории для данных и устанавливаем права
RUN mkdir -p /app/data && chown -R 32767:32767 /app/data && chmod -R 777 /app/data

# Копируем сначала только requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем все файлы, кроме директории data
COPY . .
RUN rm -rf /app/data/*

CMD ["python", "main.py"] 