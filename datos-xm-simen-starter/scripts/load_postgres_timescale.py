import os, click, pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
from glob import glob

def list_parquet_files(parquet_dir):
    return sorted([p for p in glob(os.path.join(parquet_dir, "**", "*.parquet"), recursive=True)])

def map_dtype(dtype):
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    return "TEXT"

@click.command()
@click.option("--parquet-dir", required=True)
@click.option("--pg-host", default="localhost")
@click.option("--pg-port", default=5432, type=int)
@click.option("--pg-user", default="postgres")
@click.option("--pg-password", default="postgres")
@click.option("--pg-db", default="energy")
@click.option("--schema", default="energy")
@click.option("--table", default="demanda_horaria")
@click.option("--time-col", default="fecha", help="Columna temporal para hypertable")
def main(parquet_dir, pg_host, pg_port, pg_user, pg_password, pg_db, schema, table, time_col):
    files = list_parquet_files(parquet_dir)
    if not files:
        raise click.ClickException(f"No hay parquet en {parquet_dir}")
    # inspecciona esquema
    sample = pd.read_parquet(files[0], engine="pyarrow")
    cols = [(c, map_dtype(sample[c].dtype)) for c in sample.columns]
    if time_col not in sample.columns:
        raise click.ClickException(f"'{time_col}' no está en columnas: {sample.columns}")
    ddl_cols = ", ".join([f'"{c}" {t}' for c, t in cols])
    with psycopg2.connect(host=pg_host, port=pg_port, user=pg_user, password=pg_password, dbname=pg_db) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
        cur.execute(f'CREATE TABLE IF NOT EXISTS "{schema}"."{table}" ({ddl_cols});')
        # hypertable
        cur.execute(f"SELECT create_hypertable('"{schema}"."{table}"','{time_col}', if_not_exists => TRUE);")
        # simple upsert: borra rango y vuelve a cargar (para demo)
        for f in files:
            df = pd.read_parquet(f, engine="pyarrow")
            df.columns = [c.lower() for c in df.columns]
            # COPY es rápido
            tmp_csv = f + ".csv"
            df.to_csv(tmp_csv, index=False)
            with open(tmp_csv, "r", encoding="utf-8") as fh:
                cur.copy_expert(sql=f'COPY "{schema}"."{table}" FROM STDIN WITH (FORMAT CSV, HEADER TRUE)', file=fh)
            os.remove(tmp_csv)
    print("Carga a Timescale finalizada.")

if __name__ == "__main__":
    main()
