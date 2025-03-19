FROM python:3.11-slim

WORKDIR /app


# Копируем сначала только requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем все файлы, кроме директории data
COPY . .

CMD ["python", "main.py"] 