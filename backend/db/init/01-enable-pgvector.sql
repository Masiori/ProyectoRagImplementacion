-- ============================================================
-- Inicialización de PostgreSQL
-- Este script se ejecuta automáticamente al crear la base de datos
-- por primera vez (gracias a docker-entrypoint-initdb.d).
-- ============================================================

-- Habilitar la extensión pgvector para almacenar embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar extensión para generar UUIDs (usada por SQLAlchemy)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verificación: imprime las extensiones instaladas en los logs
DO $$
BEGIN
    RAISE NOTICE 'Extensiones instaladas: vector=%, uuid-ossp=%',
        (SELECT extversion FROM pg_extension WHERE extname = 'vector'),
        (SELECT extversion FROM pg_extension WHERE extname = 'uuid-ossp');
END $$;
