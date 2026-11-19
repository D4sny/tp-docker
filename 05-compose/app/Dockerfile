FROM python:3.12-slim

WORKDIR /app

# 1) D'abord les dépendances : cette couche est mise en cache
#    tant que requirements.txt ne change pas -> rebuilds rapides
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Puis le code (change souvent)
COPY . .

# Bonne pratique sécurité : ne pas tourner en root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app:app"]
