#!/bin/bash

# ========================================
# Script de Deploy Automático
# Bot de Telegram - I_am_poor
# ========================================

set -e  # Detener si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="$HOME/I_am_poor"
SERVICE_NAME="telegram-bot"
VENV_PATH="$PROJECT_DIR/venv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 Iniciando Deploy Automático${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Verificar que estamos en el directorio correcto
echo -e "${YELLOW}📂 Navegando al directorio del proyecto...${NC}"
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: No se encontró el directorio $PROJECT_DIR${NC}"
    exit 1
}
echo -e "${GREEN}✅ Directorio: $(pwd)${NC}\n"

# 2. Detener el servicio
echo -e "${YELLOW}🛑 Deteniendo el bot...${NC}"
sudo systemctl stop "$SERVICE_NAME" || {
    echo -e "${RED}⚠️  Advertencia: El servicio no estaba corriendo${NC}"
}
echo -e "${GREEN}✅ Bot detenido${NC}\n"

# 3. Hacer backup del .env (por si acaso)
if [ -f .env ]; then
    echo -e "${YELLOW}💾 Haciendo backup de .env...${NC}"
    cp .env .env.backup
    echo -e "${GREEN}✅ Backup creado${NC}\n"
fi

# 4. Pull del repositorio
echo -e "${YELLOW}📥 Descargando cambios del repositorio...${NC}"
git pull || {
    echo -e "${RED}❌ Error al hacer git pull${NC}"
    echo -e "${YELLOW}🔄 Intentando reiniciar el servicio...${NC}"
    sudo systemctl start "$SERVICE_NAME"
    exit 1
}
echo -e "${GREEN}✅ Código actualizado${NC}\n"

# 5. Activar entorno virtual y actualizar dependencias
echo -e "${YELLOW}📦 Verificando dependencias...${NC}"
source "$VENV_PATH/bin/activate" || {
    echo -e "${RED}❌ Error al activar el entorno virtual${NC}"
    exit 1
}

# Verificar si requirements.txt cambió
if git diff HEAD@{1} HEAD --name-only | grep -q "requirements.txt"; then
    echo -e "${YELLOW}📦 requirements.txt cambió, actualizando dependencias...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencias actualizadas${NC}\n"
else
    echo -e "${GREEN}✅ No hay cambios en dependencias${NC}\n"
fi

# 6. Reiniciar el servicio
echo -e "${YELLOW}🚀 Reiniciando el bot...${NC}"
sudo systemctl start "$SERVICE_NAME" || {
    echo -e "${RED}❌ Error al iniciar el servicio${NC}"
    exit 1
}

# Esperar 2 segundos para que inicie
sleep 2

# 7. Verificar estado
echo -e "${YELLOW}🔍 Verificando estado del servicio...${NC}"
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Bot iniciado correctamente${NC}\n"
    
    # Mostrar últimas líneas del log
    echo -e "${BLUE}📋 Últimas 10 líneas del log:${NC}"
    echo -e "${BLUE}========================================${NC}"
    tail -n 10 "$PROJECT_DIR/bot.log" 2>/dev/null || echo "No hay logs disponibles aún"
    echo -e "${BLUE}========================================${NC}\n"
else
    echo -e "${RED}❌ El bot no se inició correctamente${NC}"
    echo -e "${YELLOW}📋 Últimas líneas del error log:${NC}"
    tail -n 20 "$PROJECT_DIR/bot_error.log" 2>/dev/null || sudo journalctl -u "$SERVICE_NAME" -n 20
    exit 1
fi

# 8. Resumen final
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deploy completado exitosamente${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}📊 Estado del servicio:${NC}"
sudo systemctl status "$SERVICE_NAME" --no-pager -l

echo -e "\n${YELLOW}💡 Comandos útiles:${NC}"
echo -e "  Ver logs en tiempo real: ${BLUE}tail -f $PROJECT_DIR/bot.log${NC}"
echo -e "  Ver errores:             ${BLUE}tail -f $PROJECT_DIR/bot_error.log${NC}"
echo -e "  Ver estado:              ${BLUE}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  Reiniciar:               ${BLUE}sudo systemctl restart $SERVICE_NAME${NC}\n"
