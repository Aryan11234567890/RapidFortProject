FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    fonts-liberation \
    && apt-get clean
RUN apt-get install libpq-dev -y
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
