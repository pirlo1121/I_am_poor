# 💰 Asistente Financiero Personal - Telegram Bot

Bot de Telegram con IA que funciona como tu asistente financiero personal. Usa **Gemini o ChatGPT** para interpretar lenguaje natural y gestionar gastos en **Supabase**.

## 🚀 Características

- ✅ **Registro de gastos en lenguaje natural**: "Gasté 20k en uvas"
- ✅ **Consultas inteligentes**: "¿Cuánto gasté esta semana?"
- ✅ **Gastos fijos y mensualidades**: Trackeo automático de facturas
- ✅ **IA conversacional** con personalidad sarcástica
- ✅ **Soporte dual**: Gemini o ChatGPT
- ✅ **Base de datos**: PostgreSQL vía Supabase

---

## 📋 Requisitos

1. **Python 3.10+**
2. **Bot de Telegram** (crear en [@BotFather](https://t.me/botfather))
3. **API Key** de Gemini ([obtener aquí](https://makersuite.google.com/app/apikey)) o ChatGPT ([obtener aquí](https://platform.openai.com/account/api-keys))
4. **Cuenta de Supabase** ([crear aquí](https://supabase.com))

---

## 🛠️ Instalación Rápida

### 1. Crear las tablas en Supabase

En tu proyecto de Supabase, ve a **SQL Editor** y ejecuta:

```sql
-- Tabla de gastos variables
CREATE TABLE gastos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL
);

-- Tabla de gastos fijos mensuales
CREATE TABLE gastos_fijos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT NOT NULL,
  amount FLOAT NOT NULL,
  category TEXT NOT NULL,
  day_of_month INTEGER NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

-- Tabla de pagos realizados (tracking de mensualidades)
CREATE TABLE pagos_realizados (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  gasto_fijo_id BIGINT REFERENCES gastos_fijos(id),
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  amount FLOAT NOT NULL
);
```

### 2. Configurar el proyecto

```bash
# Clonar el repositorio o entrar al directorio
cd I_am_poor

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
```

### 3. Editar `.env` con tus credenciales

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=tu_token_de_telegram

# AI Provider (elige uno)
AI_PROVIDER=gemini  # o "chatgpt"
GEMINI_API_KEY=tu_api_key_de_gemini  # Si usas Gemini
CHATGPT_API_KEY=tu_api_key_de_chatgpt  # Si usas ChatGPT

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=tu_supabase_anon_key
```

### 4. Ejecutar el bot

```bash
python bot.py
```

Deberías ver:
```
INFO - ✅ Conexión a Supabase establecida exitosamente
INFO - 🚀 Bot iniciado correctamente. Esperando mensajes...
```

---

## 💬 Cómo Usar

### Comandos

- `/start` - Iniciar el bot
- `/help` - Ver ayuda
- `/gastos` - Últimos 5 gastos
- `/resumen` - Resumen del mes
- `/facturas` - Ver mensualidades

### Ejemplos

**Registrar gastos:**
```
Tú: Gasté 20k en uvas
Bot: 💰 Listo, registré $20,000 en comida

Tú: Pagué 50 mil de Uber
Bot: ✅ Anotado: $50,000 en transporte
```

**Gastos fijos:**
```
Tú: Registra el arriendo de 800 mil cada 5 de mes
Bot: ✅ Gasto fijo registrado: Arriendo - $800,000 cada día 5

Tú: Arriendo pagado
Bot: ✅ Marcado como pagado: Arriendo - $800,000
```

**Consultas:**
```
Tú: ¿Cuánto gasté hoy?
Bot: 📊 Hoy gastaste $70,000 en 3 gastos

Tú: ¿Qué facturas tengo pendientes?
Bot: 📋 Facturas Pendientes:
     1. Internet - $80,000 (Vence: 10 de febrero)
     2. Luz - $120,000 (Vence HOY)
```

**Análisis con presupuesto:**
```
Tú: Suma gastos y mensualidades, réstalos de 3 millones
Bot: 💰 Resumen Financiero:
     Gastos: $245,000
     Mensualidades Pagadas: $1,472,000
     Total Gastado: $1,717,000
     
     Balance: $1,283,000 disponibles ✅ (42.8% restante)
```

---

## 📁 Estructura del Proyecto

```
I_am_poor/
├── bot.py                    # Entry point
├── database.py               # Operaciones con Supabase
│
├── config/
│   └── settings.py          # Configuración y env vars
│
├── ai/
│   ├── prompts.py           # System instructions
│   ├── tools.py             # Función declarations
│   └── providers.py         # Wrapper Gemini/ChatGPT
│
├── handlers/
│   ├── commands.py          # Comandos de Telegram
│   └── messages.py          # Handler de mensajes
│
├── core/
│   └── session_manager.py   # Gestión de sesiones
│
└── requirements.txt
```

---

## 🐛 Solución de Problemas

**Error: "TELEGRAM_BOT_TOKEN no configurado"**
- Verifica que el archivo `.env` existe
- Asegúrate de que el token es correcto (sin espacios)

**Error: "Error al conectar con Supabase"**
- Verifica que las tablas existen en Supabase
- Confirma que `SUPABASE_URL` y `SUPABASE_KEY` son correctos

**El bot no responde:**
- Verifica que está ejecutándose sin errores
- Busca tu bot en Telegram y envía `/start`
- Revisa los logs en la consola

---

## 🎯 Categorías Disponibles

- `comida` - Alimentación
- `transporte` - Uber, bus, etc.
- `entretenimiento` - Netflix, cine, etc.
- `servicios` - Internet, luz, agua
- `salud` - Medicina, doctor
- `mercado` - Compras grandes (D1, ARA, Éxito)
- `general` - Otros gastos

---

## � Notas

- El bot mantiene **hasta 20 intercambios** de contexto conversacional
- Usa **función optimizada** para cálculos complejos (más rápido)
- **Personalidad sarcástica**: Solo responde temas financieros

---

**Desarrollado con ❤️ usando Python, Gemini AI y Supabase**
