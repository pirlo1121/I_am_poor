#!/bin/bash

# Script para iniciar el bot de manera segura (sin duplicados)

# Ir al directorio del proyecto
cd /home/pirlo/Desktop/data/projects/I_am_poor

# Matar cualquier instancia previa del bot
echo "🔍 Verificando instancias previas..."
pkill -f "python.*bot.py"
sleep 1

# Verificar que no haya procesos corriendo
RUNNING=$(ps aux | grep "[p]ython.*bot.py" | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "⚠️  Aún hay instancias corriendo, forzando terminación..."
    pkill -9 -f "python.*bot.py"
    sleep 1
fi

# Activar entorno virtual e iniciar bot
echo "🚀 Iniciando bot..."
source venv/bin/activate
python3 bot.py > bot_output.log 2>&1 &

sleep 2

# Verificar que solo haya una instancia
RUNNING=$(ps aux | grep "[p]ython.*bot.py" | wc -l)
echo "✅ Instancias del bot corriendo: $RUNNING"

if [ $RUNNING -eq 1 ]; then
    echo "✅ Bot iniciado correctamente (una sola instancia)"
    ps aux | grep "[p]ython.*bot.py"
elif [ $RUNNING -gt 1 ]; then
    echo "⚠️  ADVERTENCIA: Hay $RUNNING instancias corriendo!"
    ps aux | grep "[p]ython.*bot.py"
else
    echo "❌ ERROR: El bot no se inició correctamente"
fi
