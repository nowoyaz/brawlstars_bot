FROM python:3.11-slim

WORKDIR /app

# Создаем директории для данных и устанавливаем права
RUN mkdir -p /app/data && chown -R 32767:32767 /app/data && chmod -R 777 /app/data

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"] 