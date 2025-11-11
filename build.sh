#!/usr/bin/env bash

set -o errexit

echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completo!"
echo "ℹ️  Banco de dados será inicializado no primeiro start (runtime)"
