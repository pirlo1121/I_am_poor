# 🚀 Script de Deploy Automático

Este script automatiza el proceso de actualización del bot en producción.

## 📋 ¿Qué hace el script?

1. ✅ **Detiene el bot** de forma segura
2. ✅ **Hace git pull** del repositorio
3. ✅ **Hace backup del .env** (por seguridad)
4. ✅ **Actualiza dependencias** (solo si requirements.txt cambió)
5. ✅ **Reinicia el bot**
6. ✅ **Verifica que esté corriendo** correctamente
7. ✅ **Muestra los logs** recientes

## 🔧 Uso

### En el servidor (Lightsail/EC2):

```bash
# Ejecutar el script
./deploy.sh

# O con bash explícito
bash deploy.sh
```

## 📝 Prerequisitos

Antes de usar el script, asegúrate de tener:

- [x] Git configurado en el servidor
- [x] Repositorio clonado en `~/I_am_poor`
- [x] Servicio systemd llamado `telegram-bot`
- [x] Entorno virtual en `~/I_am_poor/venv`

## 🎯 Flujo de trabajo recomendado

### Desarrollo local:

```bash
# 1. Hacer cambios en tu código local
# 2. Testear localmente
python bot.py

# 3. Commit y push a Git
git add .
git commit -m "Mejora en la funcionalidad X"
git push origin main
```

### Deploy en producción:

```bash
# SSH al servidor
ssh -i key.pem admin@TU_IP

# Ejecutar deploy
cd I_am_poor
./deploy.sh
```

¡Listo! El script se encarga del resto.

## 🛡️ Seguridad

El script incluye:

- ✅ Manejo de errores (si algo falla, no rompe el bot)
- ✅ Backup automático del `.env`
- ✅ Verificación de estado antes de terminar
- ✅ Logs detallados de cada paso

## 🐛 Si algo sale mal

El script intentará reiniciar el bot automáticamente si falla el git pull.

Ver logs de error:
```bash
tail -f ~/I_am_poor/bot_error.log
sudo journalctl -u telegram-bot -n 50
```

Reiniciar manualmente:
```bash
sudo systemctl restart telegram-bot
sudo systemctl status telegram-bot
```

## 💡 Tips

- El script solo actualiza dependencias si `requirements.txt` cambió (ahorra tiempo)
- Hace backup del `.env` en `.env.backup` antes de actualizar
- Muestra los últimos 10 logs al finalizar para verificar que todo está bien

## 🎨 Output del script

El script usa colores para facilitar la lectura:
- 🔵 **Azul**: Información general
- 🟡 **Amarillo**: Acciones en progreso
- 🟢 **Verde**: Éxito
- 🔴 **Rojo**: Errores

## 📦 Personalización

Si tu configuración es diferente, edita estas variables al inicio del script:

```bash
PROJECT_DIR="$HOME/I_am_poor"      # Ruta del proyecto
SERVICE_NAME="telegram-bot"         # Nombre del servicio systemd
VENV_PATH="$PROJECT_DIR/venv"      # Ruta del virtualenv
```
