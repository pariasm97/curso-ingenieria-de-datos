-- Habilitar extensión y crear hypertable manualmente (alternativa al script Python)
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE SCHEMA IF NOT EXISTS energy;
CREATE TABLE IF NOT EXISTS energy.demanda_horaria (
  fecha TIMESTAMP,
  region TEXT,
  valor DOUBLE PRECISION
);
SELECT create_hypertable('energy.demanda_horaria','fecha', if_not_exists=>true);
