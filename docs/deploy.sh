#!/bin/bash

# ========================================
# Script de Deploy Automático con Docker
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 Iniciando Deploy Automático (Docker)${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Verificar que estamos en el directorio correcto
echo -e "${YELLOW}📂 Navegando al directorio del proyecto...${NC}"
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: No se encontró el directorio $PROJECT_DIR${NC}"
    exit 1
}
echo -e "${GREEN}✅ Directorio: $(pwd)${NC}\n"

# 2. Detener servicio antiguo si existe y está corriendo
if systemctl list-units --full -all | grep -Fq "telegram-bot.service"; then
    echo -e "${YELLOW}🛑 Deteniendo el servicio antiguo de systemd (telegram-bot)...${NC}"
    sudo systemctl stop telegram-bot 2>/dev/null || true
    sudo systemctl disable telegram-bot 2>/dev/null || true
fi

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
    exit 1
}
echo -e "${GREEN}✅ Código actualizado${NC}\n"

# 5. Reconstruir e iniciar los contenedores
echo -e "${YELLOW}📦 Construyendo e iniciando contenedores con Docker Compose...${NC}"
docker compose up -d --build || {
    echo -e "${RED}❌ Error al ejecutar Docker Compose${NC}"
    exit 1
}
echo -e "${GREEN}✅ Contenedores iniciados exitosamente${NC}\n"

# Esperar 2 segundos para que inicien bien
sleep 2

# 6. Resumen final
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deploy completado exitosamente${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}📊 Estado de los contenedores:${NC}"
docker compose ps

echo -e "\n${YELLOW}💡 Comandos útiles:${NC}"
echo -e "  Ver logs del bot:     ${BLUE}docker compose logs -f bot${NC}"
echo -e "  Ver logs del backend: ${BLUE}docker compose logs -f back${NC}"
echo -e "  Ver estado:           ${BLUE}docker compose ps${NC}"
echo -e "  Detener todo:         ${BLUE}docker compose down${NC}"
echo -e "  Reiniciar todo:       ${BLUE}docker compose restart${NC}\n"
