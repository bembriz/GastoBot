-- Ejemplo de schema SQL para referencia (NO ejecutar directamente, usar Alembic)
-- Este archivo es solo documentacion del diseno esperado

-- ============================================================
-- Tabla: users
-- PRD §4, §18
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'standard')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_change_required BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- ============================================================
-- Tabla: expense_records
-- PRD §11, §12, §17
-- ============================================================
CREATE TABLE IF NOT EXISTS expense_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    image_hash VARCHAR(64) NOT NULL,
    transaction_date DATE,
    amount NUMERIC(12,2),
    ticket_description TEXT,
    bank VARCHAR(100),
    transaction_type VARCHAR(20) CHECK (transaction_type IN ('Transferencia', 'Credito')),
    confidence_json JSONB,
    group_code VARCHAR(50),
    consecutive INTEGER,
    final_description TEXT,
    category_id UUID,
    account_id UUID,
    status VARCHAR(30) NOT NULL DEFAULT 'DETECTADO',
    sheet_name VARCHAR(100),
    sheet_row INTEGER,
    source_filename VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_expense_records_status ON expense_records(status);
CREATE INDEX IF NOT EXISTS ix_expense_records_owner_id ON expense_records(owner_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_expense_records_image_hash ON expense_records(image_hash);
CREATE UNIQUE INDEX IF NOT EXISTS ix_expense_records_group_consecutive
    ON expense_records(group_code, consecutive)
    WHERE group_code IS NOT NULL AND consecutive IS NOT NULL;

-- ============================================================
-- Tabla: processing_queue
-- PRD §9.2 - CRITICO: indice para reclamo FIFO atomico
-- ============================================================
CREATE TABLE IF NOT EXISTS processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID UNIQUE NOT NULL REFERENCES expense_records(id) ON DELETE CASCADE,
    enqueued_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    claimed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    worker_id VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'EN_COLA',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    last_error TEXT
);

-- INDICE CRITICO: ordena por enqueued_at ASC, record_id ASC para FIFO estricto
CREATE INDEX IF NOT EXISTS ix_processing_queue_status_enqueued
    ON processing_queue(status, enqueued_at ASC, record_id ASC);

-- ============================================================
-- Tabla: audit_events
-- PRD §21
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    record_id UUID REFERENCES expense_records(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    old_state JSONB,
    new_state JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_events_record_id ON audit_events(record_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_actor_id ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events(created_at);
