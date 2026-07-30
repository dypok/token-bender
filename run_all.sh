#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "=== Optimizador de Tokens - Instalación y Arranque ==="
echo ""

# 1. Verificar e instalar dependencias del Backend
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual en backend/venv..."
    python3 -m venv venv
fi

echo "Verificando dependencias Python..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 2. Verificar dependencias del Frontend
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
    echo "Instalando paquetes de Node.js en frontend..."
    npm install
fi

# 3. Detener instancias anteriores si están corriendo
echo ""
echo "Deteniendo procesos anteriores en puerto 8000 y 5173..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true

# 4. Iniciar Servidores
echo ""
echo "Iniciando Backend Uvicorn (http://localhost:8000)..."
cd "$ROOT/backend"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Iniciando Frontend Vite (http://localhost:5173)..."
cd "$ROOT/frontend"
npm run dev -- --port 5173 &
FRONTEND_PID=$!

echo ""
echo "========================================================="
echo " App iniciada con éxito!"
echo " Backend API:  http://localhost:8000"
echo " Frontend UI:   http://localhost:5173"
echo " Presiona Ctrl+C para detener ambos servidores."
echo "========================================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
