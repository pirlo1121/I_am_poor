-- ============================================
-- Script SQL para crear tablas del Bot Financiero
-- ============================================

-- 1. ELIMINAR TABLAS EXISTENTES (si necesitas empezar limpio)
-- Descomentar solo si quieres resetear todo
-- DROP TABLE IF EXISTS pagos_realizados CASCADE;
-- DROP TABLE IF EXISTS gastos_fijos CASCADE;
-- DROP TABLE IF EXISTS gastos CASCADE;

-- ============================================
-- 2. CREAR TABLA GASTOS (Principal)
-- ============================================
CREATE TABLE IF NOT EXISTS gastos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL
);

-- ============================================
-- 3. CREAR TABLA GASTOS FIJOS (Recurrentes)
-- ============================================
CREATE TABLE IF NOT EXISTS gastos_fijos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT NOT NULL,
  amount FLOAT NOT NULL,
  category TEXT NOT NULL,
  day_of_month INTEGER NOT NULL CHECK (day_of_month >= 1 AND day_of_month <= 31),
  active BOOLEAN DEFAULT TRUE,
  
  -- Índices para mejorar queries
  CONSTRAINT valid_day_range CHECK (day_of_month BETWEEN 1 AND 31)
);

-- Índice para búsquedas rápidas por estado activo
CREATE INDEX IF NOT EXISTS idx_gastos_fijos_active ON gastos_fijos(active);

-- ============================================
-- 4. CREAR TABLA PAGOS REALIZADOS (Tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS pagos_realizados (
  id BIGSERIAL PRIMARY KEY,
  gasto_fijo_id BIGINT NOT NULL REFERENCES gastos_fijos(id) ON DELETE CASCADE,
  paid_at TIMESTAMPTZ DEFAULT NOW(),
  month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
  year INTEGER NOT NULL CHECK (year >= 2020),
  amount FLOAT NOT NULL,
  
  -- Evitar pagos duplicados del mismo gasto en el mismo mes
  UNIQUE(gasto_fijo_id, month, year)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_pagos_gasto_fijo ON pagos_realizados(gasto_fijo_id);
CREATE INDEX IF NOT EXISTS idx_pagos_month_year ON pagos_realizados(month, year);

-- ============================================
-- 5. NUEVAS TABLAS - SISTEMA DE METAS DE AHORRO
-- ============================================
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

-- Índice para búsquedas rápidas por estado activo
CREATE INDEX IF NOT EXISTS idx_savings_goals_active ON savings_goals(active);

-- Tabla de contribuciones a metas de ahorro
CREATE TABLE IF NOT EXISTS savings_contributions (
  id BIGSERIAL PRIMARY KEY,
  goal_id BIGINT NOT NULL REFERENCES savings_goals(id) ON DELETE CASCADE,
  amount FLOAT NOT NULL,
  contributed_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT
);

-- Índice para búsquedas rápidas por meta
CREATE INDEX IF NOT EXISTS idx_contributions_goal ON savings_contributions(goal_id);

-- ============================================
-- 6. CREAR TABLA INGRESOS (Salario + Extras)
-- ============================================
CREATE TABLE IF NOT EXISTS ingresos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  amount FLOAT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('salario', 'extra')),
  description TEXT,
  month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
  year INTEGER NOT NULL CHECK (year >= 2020)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_ingresos_type ON ingresos(type);
CREATE INDEX IF NOT EXISTS idx_ingresos_month_year ON ingresos(month, year);

-- ============================================
-- 7. VERIFICAR TABLAS CREADAS
-- ============================================
SELECT 'Tablas creadas exitosamente!' as status;

-- Ver estructura de gastos
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'gastos';

-- Ver estructura de gastos_fijos
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'gastos_fijos';

-- Ver estructura de pagos_realizados
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pagos_realizados';

-- Ver estructura de savings_goals
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'savings_goals';

-- Ver estructura de savings_contributions
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'savings_contributions';
