#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "=== Optimizador de Tokens - Inicio Backend con Logs ==="
echo ""

cd "$ROOT/backend"

# 1. Verificar entorno virtual y dependencias
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual en backend/venv..."
    python3 -m venv venv
fi

echo "Verificando e instalando dependencias en backend/venv..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 2. Liberar puerto 8000 si está ocupado
echo ""
echo "Liberando puerto 8000 si existía proceso previo..."
fuser -k 8000/tcp 2>/dev/null || true

# 3. Iniciar servidor Uvicorn con logs en consola
echo ""
echo "========================================================="
echo " Servidor Backend corriendo en: http://0.0.0.0:8000"
echo " Viendo logs en vivo (Presiona Ctrl+C para detener)"
echo "========================================================="
echo ""

./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
