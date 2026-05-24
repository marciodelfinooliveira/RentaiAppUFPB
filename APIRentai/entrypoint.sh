#!/bin/sh

set -e

echo "Aguardando o PostgreSQL iniciar..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL iniciado com sucesso!"

echo "Aplicando migrações do banco de dados..."
alembic upgrade head
echo "Migrações aplicadas com sucesso!"

echo "Iniciando a aplicação..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
