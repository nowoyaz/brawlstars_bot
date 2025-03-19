FROM python:3.11-slim

WORKDIR /app

# Создаем директории для данных
RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Устанавливаем права на директории
RUN chmod -R 777 /app/data

CMD ["python", "main.py"] 