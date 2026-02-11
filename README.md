# 💰 Asistente Financiero Personal - Telegram Bot

Bot de Telegram con IA que funciona como un asistente financiero personal. Utiliza **Gemini Pro** con Function Calling para interpretar lenguaje natural y gestionar gastos en una base de datos **PostgreSQL (Supabase)**.

## 🚀 Características

- ✅ **Registro de gastos mediante lenguaje natural** (ej: "Gasté 20k en uvas")
- ✅ **Consulta de gastos recientes** con formato amigable
- ✅ **IA conversacional** usando Gemini Pro con System Instructions
- ✅ **Function Calling** para ejecutar acciones automáticamente
- ✅ **Base de datos PostgreSQL** vía Supabase
- ✅ **Manejo robusto de errores** y logging

## � Cómo Funciona el Proyecto

El bot funciona mediante un flujo de tres capas que trabajan en conjunto:

### 1️⃣ **El Usuario escribe en Telegram**
Cuando envías un mensaje como *"Gasté 20k en uvas"*, el bot lo recibe a través de `python-telegram-bot`.

### 2️⃣ **Gemini AI analiza el mensaje**
El bot envía tu mensaje a **Gemini Pro** con una instrucción especial (System Instruction) que le dice:
- "Eres un contador profesional"
- "Si el usuario menciona un gasto, llama a la función `add_expense`"
- "Si pregunta por sus gastos, llama a `get_recent_expenses`"

Gemini AI usa **Function Calling** para decidir qué hacer:

```
Usuario: "Gasté 20k en uvas"
      ↓
Gemini analiza y detecta: "El usuario gastó dinero"
      ↓
Gemini decide: add_expense(amount=20000, description="uvas", category="comida")
```

### 3️⃣ **El Bot ejecuta la función**
El código de `bot.py` recibe la instrucción de Gemini y ejecuta la función correspondiente en `database.py`:

```python
# Gemini decidió llamar a add_expense
function_name = "add_expense"
function_args = {"amount": 20000, "description": "uvas", "category": "comida"}

# El bot ejecuta la función real
result = add_expense(amount=20000, description="uvas", category="comida")
```

### 4️⃣ **Se guarda en Supabase**
La función `add_expense()` inserta el registro en la base de datos PostgreSQL:

```sql
INSERT INTO gastos (amount, description, category, created_at)
VALUES (20000, 'uvas', 'comida', NOW());
```

### 5️⃣ **El Usuario recibe confirmación**
El bot responde en Telegram:
> ✅ Gasto registrado exitosamente: $20,000 COP en comida

---

### 📊 Flujo Visual

```
┌─────────────────┐
│  Usuario        │
│  "Gasté 20k     │
│   en uvas"      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Telegram Bot   │
│  (bot.py)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini AI      │
│  Analiza y      │
│  decide función │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  database.py    │
│  add_expense()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase DB    │
│  PostgreSQL     │
└─────────────────┘
```

---

## �📋 Requisitos Previos

1. **Python 3.10+** instalado
2. **Cuenta de Telegram** y un bot creado con [@BotFather](https://t.me/botfather)
3. **API Key de Google Gemini** ([obtener aquí](https://makersuite.google.com/app/apikey))
4. **Proyecto de Supabase** con una tabla `gastos` configurada

### Estructura de la tabla `gastos` en Supabase

```sql
CREATE TABLE gastos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL
);
```

## 🛠️ Instalación

### 1. Clonar o descargar el proyecto

```bash
cd I_am_poor
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_supabase_anon_key
```

## ▶️ Cómo Ejecutar el Proyecto (Paso a Paso)

### 🔴 Paso 1: Crear tu Bot de Telegram

1. Abre Telegram y busca: **@BotFather**
2. Envía el comando: `/newbot`
3. Asigna un nombre (ej: "Mi Asistente Financiero")
4. Asigna un username (ej: "mi_asistente_financiero_bot")
5. **Copia el token** que te da BotFather (lo necesitarás en el `.env`)

### 🟠 Paso 2: Obtener API Key de Gemini

1. Ve a: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en **"Create API Key"**
4. **Copia la API Key** (la necesitarás en el `.env`)

### 🟡 Paso 3: Crear Proyecto en Supabase

1. Ve a: [Supabase](https://supabase.com)
2. Crea una cuenta o inicia sesión
3. Haz clic en **"New Project"**
4. Asigna un nombre y contraseña
5. Espera a que el proyecto se inicialice (~2 minutos)

### 🟢 Paso 4: Crear la Tabla en Supabase

1. En tu proyecto de Supabase, ve a **SQL Editor**
2. Copia y pega este código:

```sql
CREATE TABLE gastos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL
);
```

3. Haz clic en **"Run"**
4. Verifica que la tabla se creó en **"Table Editor"**

### 🔵 Paso 5: Obtener Credenciales de Supabase

1. En tu proyecto de Supabase, ve a **Settings** → **API**
2. Copia:
   - **Project URL** (ej: `https://xxxxx.supabase.co`)
   - **anon public key** (la llave larga que empieza con `eyJ...`)

### 🟣 Paso 6: Configurar Variables de Entorno

1. En el directorio del proyecto, crea un archivo `.env`:

```bash
cd /home/pirlo/Desktop/data/projects/I_am_poor
cp .env.example .env
```

2. Edita el archivo `.env` con tus credenciales reales:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### ⚫ Paso 7: Instalar Dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### ⚪ Paso 8: Ejecutar el Bot

```bash
python bot.py
```

**Salida esperada:**

```
INFO - ✅ Conexión a Supabase establecida exitosamente
INFO - 🚀 Iniciando Asistente Financiero Bot...
INFO - ✅ Bot iniciado correctamente. Esperando mensajes...
```

### ✅ Paso 9: ¡Probar el Bot!

1. Abre Telegram en tu móvil o web
2. Busca tu bot por el username que creaste (@mi_asistente_financiero_bot)
3. Envía: `/start`
4. Prueba con: `Gasté 20k en uvas`
5. Verifica la respuesta: `✅ Gasto registrado exitosamente...`
6. Prueba con: `Muéstrame mis gastos`

---

## 🐛 Solución de Problemas

### Error: "TELEGRAM_BOT_TOKEN no configurado"
- Verifica que el archivo `.env` existe y tiene el token correcto
- Asegúrate de que el token no tiene espacios al inicio o final

### Error: "Error al conectar con Supabase"
- Verifica que `SUPABASE_URL` tiene el formato: `https://xxxxx.supabase.co`
- Verifica que `SUPABASE_KEY` es la **anon public key**, no la service role key
- Asegúrate de que la tabla `gastos` existe en Supabase

### Error: "Invalid API Key" (Gemini)
- Verifica que `GEMINI_API_KEY` es válida
- Asegúrate de que la API está habilitada en Google Cloud
- Revisa tu cuota de uso en Google AI Studio

### El bot no responde en Telegram
- Verifica que el bot está ejecutándose y no hay errores en la consola
- Busca el bot por su username exacto en Telegram
- Envía `/start` para iniciar la conversación

### Errores de dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

## 💬 Uso del Bot

### Comandos disponibles:

- `/start` - Iniciar el bot
- `/help` - Ver ayuda
- `/gastos` - Ver últimos 5 gastos

### Ejemplos de conversación:

**Registrar gastos:**
```
Usuario: Gasté 20k en uvas
Bot: ✅ Gasto registrado exitosamente: $20,000 COP en comida

Usuario: Pagué 50 mil de Uber
Bot: ✅ Gasto registrado exitosamente: $50,000 COP en transporte
```

**Consultar gastos:**
```
Usuario: Muéstrame mis gastos
Bot: 📊 Últimos 5 gastos:

1. 💰 $50,000 COP
   📝 Uber
   🏷️ Categoría: Transporte
   📅 2026-02-11

2. 💰 $20,000 COP
   📝 uvas
   🏷️ Categoría: Comida
   📅 2026-02-11

💵 Total: $70,000 COP
```

## 📁 Estructura del Proyecto

```
I_am_poor/
├── bot.py              # Lógica principal del bot de Telegram
├── database.py         # Conexión a Supabase y funciones de BD
├── requirements.txt    # Dependencias del proyecto
├── .env.example        # Plantilla de variables de entorno
├── .env               # Variables de entorno (NO commitear)
└── README.md          # Esta documentación
```

## 🔧 Arquitectura

### 1. **bot.py** - Bot de Telegram + Gemini AI
- Maneja mensajes del usuario
- Integra Gemini Pro con Function Calling
- Define System Instruction para comportamiento del asistente
- Procesa respuestas de la IA y ejecuta funciones

### 2. **database.py** - Capa de Base de Datos
- `init_supabase()`: Inicializa conexión a Supabase
- `add_expense(amount, description, category)`: Registra gastos
- `get_recent_expenses()`: Consulta últimos 5 gastos

### 3. **Function Calling (Gemini)**
Gemini puede llamar automáticamente a:
- `add_expense`: Cuando detecta que el usuario gastó dinero
- `get_recent_expenses`: Cuando el usuario quiere ver sus gastos

## 🛡️ Manejo de Errores

El código incluye:
- ✅ Validación de variables de entorno
- ✅ Try-catch en todas las operaciones de BD
- ✅ Logging detallado
- ✅ Mensajes de error amigables al usuario
- ✅ Error handler global del bot

## 📝 Categorías de Gastos

El bot reconoce estas categorías:
- `comida`
- `transporte`
- `entretenimiento`
- `servicios`
- `salud`
- `general`

## 🚀 Próximas Mejoras

- [ ] Reportes mensuales automáticos
- [ ] Gráficos de gastos por categoría
- [ ] Presupuestos y alertas
- [ ] Exportar datos a CSV/Excel
- [ ] Soporte multi-usuario

## 📚 Documentación de APIs

- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Siéntete libre de abrir issues o pull requests.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**Desarrollado con ❤️ usando Python, Gemini AI y Supabase**
