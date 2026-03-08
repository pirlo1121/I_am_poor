# I Am Poor - Backend (API)

Este es el backend del Asistente Financiero para Telegram.
Está construido con **FastAPI** y se encarga de:
1. Conexión con Supabase (Base de datos)
2. Comunicación con los modelos de IA (Gemini / ChatGPT)
3. Ejecución de herramientas (Function Calling)

## Ejecución Local
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Documentación API
Una vez corriendo, puedes ver y probar los endpoints en la interfaz de Swagger:
`http://localhost:8000/docs`
