# 💰 Asistente Financiero Personal - Telegram Bot

> **Bot inteligente de Telegram** que te ayuda a gestionar tus finanzas personales usando inteligencia artificial. Registra gastos, trackea mensualidades, gestiona metas de ahorro y consulta tu balance conversando naturalmente — por texto o voz.

---

## ✨ Características Principales

### 🗣️ **Lenguaje Natural**
Interactúa con el bot como si hablaras con un amigo:
- "Gasté 20k en uvas" → Se registra automáticamente
- "¿Cuánto gasté esta semana?" → Obtén respuestas instantáneas
- "Arriendo pagado" → Marca facturas como pagadas

### 🎤 **Mensajes de Voz**
Envía notas de voz y el bot las transcribe automáticamente usando OpenAI Whisper, luego las procesa como texto normal.

### 📊 **Gestión Completa de Finanzas**
- ✅ **Gastos variables**: Registra, edita y elimina compras diarias
- ✅ **Gastos fijos**: Trackea mensualidades (arriendo, servicios, etc.)
- ✅ **Ingresos**: Salario fijo + ingresos extras
- ✅ **Metas de ahorro**: Crea metas con progreso visual
- ✅ **Consultas inteligentes**: Resúmenes por día, semana, mes o categoría
- ✅ **Análisis predictivo**: Proyecciones de gasto basadas en historial
- ✅ **Insights financieros**: Análisis automáticos de tus finanzas
- ✅ **Comparación mensual**: Compara gastos entre dos meses
- ✅ **Recordatorios**: Notificaciones automáticas 1 día antes de vencimiento de facturas

### 🤖 **Tecnología**
- **IA Dual**: Funciona con Gemini 2.5 Flash o ChatGPT (gpt-4o-mini)
- **Base de datos**: PostgreSQL hospedado en Supabase
- **Voz**: Transcripción con OpenAI Whisper
- **Estabilidad**: Rate Limiter, Circuit Breaker, limpieza automática de sesiones

---

## 📋 Requisitos Previos

| Requisito | Descripción | Enlace |
|-----------|-------------|--------|
| **Python 3.10+** | Lenguaje de programación | [Descargar](https://www.python.org/downloads/) |
| **Bot de Telegram** | Token del bot | [Crear con @BotFather](https://t.me/botfather) |
| **API Key de IA** | Gemini o ChatGPT | [Gemini](https://makersuite.google.com/app/apikey) \| [ChatGPT](https://platform.openai.com/account/api-keys) |
| **Cuenta Supabase** | Base de datos PostgreSQL | [Crear cuenta](https://supabase.com) |

---

## 🚀 Instalación Paso a Paso

### **Paso 1: Configurar Base de Datos**

1. Ingresa a tu proyecto en [Supabase](https://supabase.com)
2. Navega a **SQL Editor**
3. Copia y ejecuta el contenido de [`schema.sql`](schema.sql):

```sql
-- Tabla de gastos variables
CREATE TABLE IF NOT EXISTS gastos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL
);

-- Tabla de gastos fijos mensuales
CREATE TABLE IF NOT EXISTS gastos_fijos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT NOT NULL,
  amount FLOAT NOT NULL,
  category TEXT NOT NULL,
  day_of_month INTEGER NOT NULL CHECK (day_of_month >= 1 AND day_of_month <= 31),
  active BOOLEAN DEFAULT TRUE
);

-- Tabla de seguimiento de pagos
CREATE TABLE IF NOT EXISTS pagos_realizados (
  id BIGSERIAL PRIMARY KEY,
  gasto_fijo_id BIGINT NOT NULL REFERENCES gastos_fijos(id) ON DELETE CASCADE,
  paid_at TIMESTAMPTZ DEFAULT NOW(),
  month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
  year INTEGER NOT NULL CHECK (year >= 2020),
  amount FLOAT NOT NULL,
  UNIQUE(gasto_fijo_id, month, year)
);

-- Tabla de metas de ahorro
CREATE TABLE IF NOT EXISTS savings_goals (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  name TEXT NOT NULL,
  target_amount FLOAT NOT NULL,
  current_amount FLOAT DEFAULT 0,
  deadline DATE,
  category TEXT DEFAULT 'general',
  active BOOLEAN DEFAULT TRUE
);

-- Tabla de contribuciones a metas de ahorro
CREATE TABLE IF NOT EXISTS savings_contributions (
  id BIGSERIAL PRIMARY KEY,
  goal_id BIGINT NOT NULL REFERENCES savings_goals(id) ON DELETE CASCADE,
  amount FLOAT NOT NULL,
  contributed_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT
);

-- Tabla de ingresos (salario + extras)
CREATE TABLE IF NOT EXISTS ingresos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('salary', 'extra')),
  description TEXT,
  month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
  year INTEGER NOT NULL CHECK (year >= 2020)
);
```

### **Paso 2: Clonar e Instalar Dependencias**

```bash
cd I_am_poor

# Crea un entorno virtual
python -m venv venv

# Activa el entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instala las dependencias
pip install -r requirements.txt
```

### **Paso 3: Configurar Variables de Entorno**

1. Crea el archivo `.env` copiando el ejemplo:
```bash
cp .env.example .env
```

2. Edita `.env` con tus credenciales:

```env
# ═══════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ═══════════════════════════════════════
# PROVEEDOR DE IA (elige uno o ambos)
# ═══════════════════════════════════════
# Si proporcionas CHATGPT_API_KEY, se usa ChatGPT.
# Si solo proporcionas GEMINI_API_KEY, se usa Gemini.
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXX
CHATGPT_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXX

# ═══════════════════════════════════════
# SUPABASE
# ═══════════════════════════════════════
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ═══════════════════════════════════════
# RECORDATORIOS (opcional)
# ═══════════════════════════════════════
# Tu chat_id de Telegram para recibir recordatorios de facturas.
# Obtén tu chat_id enviando un mensaje a @userinfobot en Telegram.
REMINDER_CHAT_ID=123456789
```

| Variable | Obligatoria | Descripción |
|----------|:-----------:|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token de tu bot de Telegram |
| `GEMINI_API_KEY` | ⚡ | API key de Google Gemini (obligatoria si no usas ChatGPT) |
| `CHATGPT_API_KEY` | ⚡ | API key de OpenAI (también habilita transcripción de voz) |
| `SUPABASE_URL` | ✅ | URL de tu proyecto Supabase |
| `SUPABASE_KEY` | ✅ | API key pública (anon) de Supabase |
| `REMINDER_CHAT_ID` | ❌ | Chat ID para recordatorios automáticos de facturas |

### **Paso 4: Ejecutar el Bot**

```bash
python bot.py
```

✅ **Deberías ver estos mensajes:**
```
INFO - ✅ Conexión a Supabase inicializada
INFO - ⏰ Recordatorio diario de facturas programado (8:00 AM)
INFO - ✅ Bot iniciado correctamente. Esperando mensajes...
```

---

## 💬 Guía de Uso

### **Comandos Disponibles**

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra bienvenida |
| `/help` | Muestra ayuda y ejemplos de uso |
| `/gastos` | Lista los últimos 5 gastos registrados |
| `/resumen` | Resumen de gastos por categorías |
| `/facturas` | Muestra facturas pendientes del mes |

### **Ejemplos de Uso**

#### 📝 **Registrar Gastos**
```
💬 Tú: Gasté 20k en uvas
🤖 Bot: 💰 Listo, registré $20,000 en comida

💬 Tú: Pagué 50 mil de Uber
🤖 Bot: ✅ Anotado: $50,000 en transporte
```

#### 🛒 **Categorización Automática (Mercado)**
```
💬 Tú: Compré en D1 por 120 mil
🤖 Bot: 🛒 Registrado: $120,000 en mercado (D1 detectado)

💬 Tú: Fui al Éxito, 85k
🤖 Bot: 🛍️ Anotado: $85,000 en mercado
```

> Tiendas reconocidas automáticamente: **D1, ARA, Éxito, Olímpica, Carulla, Jumbo**

#### 🔁 **Gestionar Gastos Fijos**
```
💬 Tú: Registra el arriendo de 800 mil cada 5 de mes
🤖 Bot: ✅ Gasto fijo registrado: Arriendo - $800,000 cada día 5

💬 Tú: Arriendo pagado
🤖 Bot: ✅ Marcado como pagado: Arriendo

💬 Tú: Qué facturas ya pagué?
🤖 Bot: ✅ Facturas Pagadas: Arriendo ($800,000), Internet ($60,000)

💬 Tú: Ver todas las facturas
🤖 Bot: 📋 Mensualidades 2/2026:
       ✅ Arriendo - $800,000 (pagado)
       ⏰ Luz - $120,000 (vence día 18)
```

#### 💵 **Ingresos**
```
💬 Tú: Mi salario son 2 millones
🤖 Bot: ✅ Salario registrado: $2,000,000

💬 Tú: Me ingresaron 40k por vender algo
🤖 Bot: ✅ Extra registrado: $40,000 (vender algo)

💬 Tú: Cuánto he ganado este mes?
🤖 Bot: 💰 Ingresos 2/2026:
       🏢 Salario: $2,000,000
       💸 Extras: $40,000
       🚀 TOTAL: $2,040,000
```

#### 🎯 **Metas de Ahorro**
```
💬 Tú: Quiero ahorrar 5 millones para vacaciones
🤖 Bot: 🎯 Meta creada: Vacaciones ($5,000,000)

💬 Tú: Ahorré 200k para vacaciones
🤖 Bot: ✅ Aporte de $200,000 a 'Vacaciones'. Nuevo total: $200,000

💬 Tú: Ver mis metas
🤖 Bot: 🎯 Metas de Ahorro:
       Vacaciones: $200,000 / $5,000,000 (4.0%)
       [██░░░░░░░░]
```

#### 📊 **Consultas y Análisis**
```
💬 Tú: Cuánto gasté en comida?
🤖 Bot: 📊 Gastos en Comida (2/2026): $185,000 (8 gastos)

💬 Tú: Compara enero y febrero
🤖 Bot: ⚖️ Comparación 1/2026 vs 2/2026:
       📅 1/2026: $1,200,000 (45 gastos)
       📅 2/2026: $980,000 (38 gastos)
       📉 Diferencia: -$220,000 (-18.3%)

💬 Tú: Cuánto voy a gastar este mes?
🤖 Bot: 🔮 Proyección: $1,150,000 (basado en promedio de 3 meses)

💬 Tú: Análisis de mis finanzas
🤖 Bot: 💡 Insights Financieros:
       📊 Gastos totales: $980,000
       🏆 Mayor gasto: Comida con $350,000 (36%)
       📉 vs. mes anterior: -$220,000 (-18.3%)
       ⚠️ 3 facturas pendientes por $275,000
```

#### ⏰ **Recordatorios Automáticos**
El bot envía recordatorios automáticos a las **8:00 AM** un día antes de que venzan tus facturas:
```
🤖 Bot: ⏰ Recordatorio de Facturas

📋 Las siguientes facturas vencen mañana:

• Internet - $60,000 (día 18)
• Celular - $45,000 (día 18)

💰 Total: $105,000

💡 Recuerda marcarlas como pagadas cuando las pagues.
```

---

### **🎯 Categorías Disponibles**

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| 🍔 **comida** | Alimentación y restaurantes | Snacks, restaurantes, café |
| 🚗 **transporte** | Movilidad | Uber, taxi, bus, gasolina |
| 🎬 **entretenimiento** | Ocio y diversión | Netflix, cine, videojuegos |
| 💡 **servicios** | Utilidades del hogar | Internet, luz, agua, gas |
| ⚕️ **salud** | Gastos médicos | Medicina, doctor, exámenes |
| 🛒 **mercado** | Supermercado | D1, ARA, Éxito, Carulla |
| 📦 **general** | Otros gastos | Todo lo demás |

---

## 📁 Arquitectura del Proyecto

```
I_am_poor/
│
├── 🤖 bot.py                    # Punto de entrada + Jobs programados (recordatorios)
├── 🗄️ database.py               # Operaciones CRUD con Supabase
├── 🔧 utils.py                  # Circuit Breaker, Rate Limiter, transcripción de voz
├── 📄 schema.sql                # Script SQL para crear las 6 tablas
│
├── ⚙️ config/
│   ├── __init__.py              # Exporta configuración
│   └── settings.py              # Variables de entorno y configuración
│
├── 🧠 ai/
│   ├── __init__.py              # Exporta módulos AI
│   ├── prompts.py               # System instruction para la IA
│   ├── tools.py                 # Declaraciones de funciones (function calling)
│   └── providers.py             # Wrapper unificado para Gemini/ChatGPT
│
├── 📞 handlers/
│   ├── __init__.py              # Exporta handlers
│   ├── commands.py              # /start, /help, /gastos, /resumen, /facturas
│   └── messages.py              # Procesamiento de texto y voz con rate limiting
│
├── 🔧 core/
│   ├── __init__.py              # Exporta session manager
│   └── session_manager.py       # Gestión de contexto conversacional
│
├── 📦 requirements.txt          # Dependencias de Python
├── 🚀 start_bot.sh              # Script para iniciar bot sin duplicados
├── 📋 .env.example              # Plantilla de variables de entorno
└── 📋 .gitignore
```

### **Componentes Clave**

| Archivo | Función |
|---------|---------|
| `bot.py` | Inicializa el bot, registra handlers y programa jobs (recordatorios, limpieza) |
| `database.py` | Todas las operaciones CRUD: gastos, facturas, ingresos, metas, recordatorios |
| `ai/tools.py` | Define 30+ funciones que la IA puede ejecutar vía function calling |
| `ai/prompts.py` | System instruction con fecha actual y todas las capacidades |
| `ai/providers.py` | Abstracción que permite cambiar entre Gemini y ChatGPT |
| `handlers/messages.py` | Procesa mensajes de texto y voz, integra rate limiting |
| `core/session_manager.py` | Mantiene hasta 40 mensajes de historial conversacional |
| `utils.py` | Circuit Breaker, Rate Limiter, SessionManager, Whisper transcription |

---

## 🐛 Solución de Problemas Comunes

### ❌ **"TELEGRAM_BOT_TOKEN no configurado"**

**Causa:** El archivo `.env` no existe o el token está mal configurado.

**Solución:**
```bash
# Verifica que existe .env
ls -la .env

# Verifica que no hay espacios en el token
cat .env | grep TELEGRAM_BOT_TOKEN
```

---

### ❌ **"Error al conectar con Supabase"**

**Solución:**
```bash
# Verifica las variables de entorno
cat .env | grep SUPABASE

# Verifica en Supabase Dashboard:
#   - Que las 6 tablas existen
#   - Que SUPABASE_URL tiene formato: https://xxxxx.supabase.co
#   - Que SUPABASE_KEY es la "anon/public" key
```

---

### ❌ **El bot no responde**

1. Verifica que `python bot.py` está corriendo
2. Revisa los logs en la consola
3. Envía `/start` en Telegram
4. Verifica que la API key de IA es válida

---

### ❌ **"ModuleNotFoundError"**

```bash
# Asegúrate de que el entorno virtual está activado
source venv/bin/activate

# Reinstala las dependencias
pip install -r requirements.txt
```

---

### ❌ **Los recordatorios no llegan**

1. Verifica que `REMINDER_CHAT_ID` está configurado en `.env`
2. Obtén tu chat_id enviando un mensaje a `@userinfobot` en Telegram
3. El recordatorio se envía a las **8:00 AM** hora del servidor

---

## 📚 Notas Técnicas

### **🧠 Contexto Conversacional**
- El bot mantiene **hasta 40 mensajes** de historial por usuario
- Las sesiones se limpian automáticamente cada 2 horas si hay más de 50
- El historial se resetea al reiniciar el bot

### **⚡ Optimizaciones**
- **Function calling**: La IA decide qué función ejecutar basándose en el mensaje
- **Rate limiting**: Máximo 10 mensajes por minuto por usuario
- **Circuit breaker**: Previene fallos en cascada con APIs
- **Singleton DB**: Una sola conexión a Supabase reutilizada
- **Decorador @safe_db_operation**: Manejo de errores centralizado con `functools.wraps`

### **⏰ Jobs Programados**
- **Recordatorios (8:00 AM)**: Verifica facturas que vencen mañana y envía notificación
- **Limpieza de sesiones (cada 2h)**: Libera memoria de sesiones inactivas

### **🔒 Seguridad**
- Credenciales en `.env` (no versionado en Git)
- Base de datos con Row Level Security (RLS) de Supabase
- API keys nunca expuestas en logs
- Rate limiting por usuario para prevenir abuso

---

## 🛣️ Roadmap Futuro

- [x] Soporte de mensajes de voz (Whisper)
- [x] Recordatorios automáticos de facturas
- [x] Metas de ahorro con progreso visual
- [x] Ingresos (salario + extras)
- [x] Análisis predictivo y comparaciones
- [ ] Soporte multi-usuario con autenticación
- [ ] Gráficos de gastos mensuales
- [ ] Exportar reportes en PDF/Excel
- [ ] Integración con bancos (Open Banking)
- [ ] App móvil nativa

---

## 🤝 Contribuciones

¿Encontraste un bug o tienes una idea? Abre un issue o envía un pull request.

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Siéntete libre de usarlo y modificarlo.

---

<div align="center">

**Desarrollado con ❤️ usando Python, Gemini AI, ChatGPT y Supabase**

[⬆ Volver arriba](#-asistente-financiero-personal---telegram-bot)

</div>
