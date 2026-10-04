FROM python:3.12.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Должен совпадать с переменной PORT и с "Public port" в настройках
# сервиса на Northflank (раздел Networking).
EXPOSE 8000

CMD ["python", "bot.py"]
