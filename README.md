# 💰 Asistente Financiero Personal - Telegram Bot

> **Bot inteligente de Telegram** que te ayuda a gestionar tus finanzas personales usando inteligencia artificial. Registra gastos, trackea mensualidades y consulta tu balance conversando naturalmente.

---

## ✨ Características Principales

### 🗣️ **Lenguaje Natural**
Interactúa con el bot como si hablaras con un amigo:
- "Gasté 20k en uvas" → Se registra automáticamente
- "¿Cuánto gasté esta semana?" → Obtén respuestas instantáneas
- "Arriendo pagado" → Marca facturas como pagadas

### 📊 **Gestión Completa de Finanzas**
- ✅ **Gastos variables**: Registra compras diarias
- ✅ **Gastos fijos**: Trackea mensualidades (arriendo, servicios, etc.)
- ✅ **Consultas inteligentes**: Resúmenes por día, semana o mes
- ✅ **Análisis de presupuesto**: Calcula saldos disponibles
- ✅ **Categorización automática**: Organiza gastos por tipo

### 🤖 **Tecnología**
- **IA Dual**: Funciona con Gemini o ChatGPT
- **Base de datos**: PostgreSQL hospedado en Supabase
- **Personalidad**: Bot con tono sarcástico que mantiene conversaciones contextuales

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener:

| Requisito | Descripción | Enlace |
|-----------|-------------|--------|
| **Python 3.10+** | Lenguaje de programación | [Descargar](https://www.python.org/downloads/) |
| **Bot de Telegram** | Token del bot | [Crear con @BotFather](https://t.me/botfather) |
| **API Key de IA** | Gemini o ChatGPT | [Gemini](https://makersuite.google.com/app/apikey) \| [ChatGPT](https://platform.openai.com/account/api-keys) |
| **Cuenta Supabase** | Base de datos PostgreSQL | [Crear cuenta](https://supabase.com) |

---

## � Instalación Paso a Paso

### **Paso 1: Configurar Base de Datos**

1. Ingresa a tu proyecto en [Supabase](https://supabase.com)
2. Navega a **SQL Editor**
3. Copia y ejecuta el siguiente script:

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

-- Tabla de seguimiento de pagos
CREATE TABLE pagos_realizados (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  gasto_fijo_id BIGINT REFERENCES gastos_fijos(id),
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  amount FLOAT NOT NULL
);
```

### **Paso 2: Clonar e Instalar Dependencias**

```bash
# Navega al directorio del proyecto
cd I_am_poor

# Crea un entorno virtual
python -m venv venv

# Activa el entorno virtual
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

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
# ========================================
# TELEGRAM BOT
# ========================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ========================================
# PROVEEDOR DE IA (elige uno)
# ========================================
AI_PROVIDER=gemini  # Opciones: "gemini" o "chatgpt"

# Si usas Gemini:
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXX

# Si usas ChatGPT:
CHATGPT_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXX

# ========================================
# SUPABASE
# ========================================
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Paso 4: Ejecutar el Bot**

```bash
python bot.py
```

✅ **Deberías ver este mensaje:**
```
INFO - ✅ Conexión a Supabase establecida exitosamente
INFO - 🚀 Bot iniciado correctamente. Esperando mensajes...
```

---

## 💬 Guía de Uso

### **Comandos Disponibles**

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra bienvenida |
| `/help` | Muestra ayuda y ejemplos de uso |
| `/gastos` | Lista los últimos 5 gastos registrados |
| `/resumen` | Resumen financiero del mes actual |
| `/facturas` | Muestra todas las mensualidades y su estado |

### **Ejemplos de Uso**

#### 📝 **Registrar Gastos**
```
💬 Tú: Gasté 20k en uvas
🤖 Bot: 💰 Listo, registré $20,000 en comida

💬 Tú: Pagué 50 mil de Uber
🤖 Bot: ✅ Anotado: $50,000 en transporte

💬 Tú: Compré pizza por 35000
🤖 Bot: 🍕 Guardado: $35,000 en comida
```

#### 🔁 **Configurar Gastos Fijos**
```
💬 Tú: Registra el arriendo de 800 mil cada 5 de mes
🤖 Bot: ✅ Gasto fijo registrado: Arriendo - $800,000 cada día 5

💬 Tú: Netflix son 42 mil mensuales cada 15
🤖 Bot: ✅ Mensualidad creada: Netflix - $42,000 el día 15

💬 Tú: Arriendo pagado
🤖 Bot: ✅ Marcado como pagado: Arriendo - $800,000 (Febrero 2026)
```

#### 📊 **Consultas Inteligentes**
```
💬 Tú: ¿Cuánto gasté hoy?
🤖 Bot: 📊 Hoy gastaste $70,000 en 3 gastos:
       • Comida: $40,000
       • Transporte: $20,000
       • General: $10,000

💬 Tú: ¿Qué facturas tengo pendientes?
🤖 Bot: 📋 Facturas Pendientes (Febrero 2026):
       1. Internet - $80,000 (Vence: 10 de febrero)
       2. Luz - $120,000 (⚠️ Vence HOY)

💬 Tú: Muéstrame el total de la semana
🤖 Bot: 📈 Gastos de la semana (10-16 Feb):
       Total: $245,000 en 12 transacciones
```

#### 💰 **Análisis de Presupuesto**
```
💬 Tú: Suma gastos y mensualidades, réstalos de 3 millones
🤖 Bot: 💰 Resumen Financiero - Febrero 2026:
       
       📊 Gastos Variables: $245,000
       🔁 Mensualidades Pagadas: $1,472,000
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━
       💸 Total Gastado: $1,717,000
       
       💵 Presupuesto Inicial: $3,000,000
       ✅ Balance Disponible: $1,283,000 (42.8%)
```

#### 🏪 **Categorización Automática**
```
💬 Tú: Compré en D1 por 120 mil
🤖 Bot: 🛒 Registrado: $120,000 en mercado (D1 detectado)

💬 Tú: Fui al Éxito, 85k
🤖 Bot: 🛍️ Anotado: $85,000 en mercado (Éxito detectado)
```

### **🎯 Categorías Disponibles**

El bot clasifica automáticamente tus gastos en estas categorías:

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| 🍔 **comida** | Alimentación y restaurantes | Snacks, restaurantes, café |
| 🚗 **transporte** | Movilidad | Uber, taxi, bus, gasolina |
| 🎬 **entretenimiento** | Ocio y diversión | Netflix, cine, videojuegos |
| 💡 **servicios** | Utilidades del hogar | Internet, luz, agua, gas |
| ⚕️ **salud** | Gastos médicos | Medicina, doctor, examenes |
| 🛒 **mercado** | Compras grandes de supermercado | D1, ARA, Éxito, Carulla |
| 📦 **general** | Otros gastos | Todo lo demás |

---

## 📁 Arquitectura del Proyecto

```
I_am_poor/
│
├── 🤖 bot.py                    # Punto de entrada principal
├── 🗄️ database.py               # Operaciones con Supabase
│
├── ⚙️ config/
│   └── settings.py              # Variables de entorno y configuración
│
├── 🧠 ai/
│   ├── prompts.py               # Instrucciones del sistema para la IA
│   ├── tools.py                 # Declaraciones de funciones (function calling)
│   └── providers.py             # Wrapper unificado para Gemini/ChatGPT
│
├── 📞 handlers/
│   ├── commands.py              # Manejadores de comandos (/start, /help, etc.)
│   └── messages.py              # Procesamiento de mensajes de texto
│
├── 🔧 core/
│   └── session_manager.py       # Gestión de contexto conversacional
│
└── 📦 requirements.txt          # Dependencias de Python
```

### **Componentes Clave**

- **`bot.py`**: Inicializa el bot de Telegram y conecta todos los módulos
- **`database.py`**: Maneja todas las operaciones CRUD con Supabase
- **`ai/providers.py`**: Abstracción que permite cambiar entre Gemini y ChatGPT
- **`ai/tools.py`**: Define las funciones que la IA puede ejecutar (function calling)
- **`core/session_manager.py`**: Mantiene hasta 20 mensajes de historial conversacional
- **`handlers/`**: Separa la lógica de comandos y mensajes de texto

---

## 🐛 Solución de Problemas Comunes

### ❌ **"TELEGRAM_BOT_TOKEN no configurado"**

**Causa:** El archivo `.env` no existe o el token está mal configurado.

**Solución:**
```bash
# 1. Verifica que existe .env
ls -la .env

# 2. Verifica que no hay espacios en el token
cat .env | grep TELEGRAM_BOT_TOKEN

# 3. Asegúrate de que el token es válido
# Debe tener formato: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### ❌ **"Error al conectar con Supabase"**

**Causa:** Las credenciales de Supabase son incorrectas o las tablas no existen.

**Solución:**
```bash
# 1. Verifica las variables de entorno
cat .env | grep SUPABASE

# 2. Verifica en Supabase Dashboard:
#    - Que las 3 tablas existen (gastos, gastos_fijos, pagos_realizados)
#    - Que SUPABASE_URL tiene formato: https://xxxxx.supabase.co
#    - Que SUPABASE_KEY es la "anon/public" key, no la "service_role"
```

---

### ❌ **El bot no responde**

**Posibles causas y soluciones:**

1. **El bot no está ejecutándose**
   ```bash
   # Verifica que python bot.py está corriendo
   ps aux | grep bot.py
   ```

2. **Error al iniciar**
   ```bash
   # Revisa los logs en la consola
   # Busca mensajes de error en rojo
   ```

3. **Bot no iniciado en Telegram**
   - Abre Telegram y busca tu bot por su username
   - Envía `/start` para iniciar la conversación

4. **Problemas de API Key**
   ```bash
   # Verifica que la API key de IA es válida
   cat .env | grep API_KEY
   
   # Prueba la key en la consola de tu proveedor
   # Gemini: https://makersuite.google.com/app/apikey
   # ChatGPT: https://platform.openai.com/api-keys
   ```

---

### ❌ **Error: "ModuleNotFoundError"**

**Solución:**
```bash
# Asegúrate de que el entorno virtual está activado
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Reinstala las dependencias
pip install -r requirements.txt
```

---

## 📚 Notas Técnicas

### **🧠 Contexto Conversacional**
- El bot mantiene **hasta 20 intercambios** de historial
- Permite conversaciones naturales con contexto previo
- El historial se resetea al reiniciar el bot

### **⚡ Optimizaciones**
- Usa **function calling** para operaciones de base de datos
- Respuestas más rápidas que enviar todo el contexto a la IA
- Reduce costos de API tokens

### **🎭 Personalidad**
- Tono sarcástico y casual
- Solo responde a temas financieros
- Rechaza preguntas no relacionadas con finanzas

### **🔒 Seguridad**
- Las credenciales se cargan desde `.env` (no versionado en Git)
- La base de datos usa Row Level Security (RLS) de Supabase
- Las API keys nunca se exponen en logs

---

## 🛣️ Roadmap Futuro

- [ ] Soporte multi-usuario con autenticación
- [ ] Gráficos de gastos mensuales
- [ ] Exportar reportes en PDF/Excel
- [ ] Recordatorios automáticos de facturas pendientes
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

**Desarrollado con ❤️ usando Python, Gemini AI y Supabase**

[⬆ Volver arriba](#-asistente-financiero-personal---telegram-bot)

</div>
