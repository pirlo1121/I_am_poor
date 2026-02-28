# I Am Poor - Bot (Client)

Este es el cliente del Asistente Financiero para Telegram.
Está construido con **python-telegram-bot** y no tiene acceso directo a la base de datos ni a las llamadas de IA. Su única responsabilidad es:
1. Recibir mensajes (Texto / Voz) y comandos del usuario en Telegram.
2. Hacer peticiones HTTP al **Backend API**.
3. Devolver los resultados formateados al usuario en Telegram.

## Ejecución Local
```bash
## Primero debes verificar que el backend esté corriendo y escuchando.
pip install -r requirements.txt
python bot.py
```
