#!/bin/bash
# filepath: c:\Devs\python\agent_medical_ia\entrypoint.sh

set -e

# Attendre que la base de données soit prête
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Exécuter les migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Créer un superuser si nécessaire (optionnel)
# python manage.py createsuperuser --noinput

echo "Starting application..."
# Démarrer l'application
exec "$@"