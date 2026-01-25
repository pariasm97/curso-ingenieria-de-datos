import os, click, pandas as pd
from clickhouse_driver import Client
from glob import glob

def list_parquet_files(parquet_dir):
    return sorted([p for p in glob(os.path.join(parquet_dir, "**", "*.parquet"), recursive=True)])

def ch_type(dtype):
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "DateTime"
    if pd.api.types.is_integer_dtype(dtype):
        return "Int64"
    if pd.api.types.is_float_dtype(dtype):
        return "Float64"
    return "String"

@click.command()
@click.option("--parquet-dir", required=True)
@click.option("--host", default="localhost")
@click.option("--port", default=9000, type=int)
@click.option("--database", default="energy")
@click.option("--table", default="demanda_horaria")
@click.option("--time-col", default="fecha")
def main(parquet_dir, host, port, database, table, time_col):
    files = list_parquet_files(parquet_dir)
    if not files:
        raise click.ClickException(f"No hay parquet en {parquet_dir}")
    client = Client(host=host, port=port, settings={"use_numpy": True})
    client.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    sample = pd.read_parquet(files[0], engine="pyarrow")
    if time_col not in sample.columns:
        raise click.ClickException(f"'{time_col}' no está en columnas: {sample.columns}")
    cols = [(c, ch_type(sample[c].dtype)) for c in sample.columns]
    ddl_cols = ", ".join([f"`{c}` {t}" for c, t in cols])
    client.execute(f"CREATE TABLE IF NOT EXISTS {database}.{table} ({ddl_cols}) ENGINE = MergeTree PARTITION BY toYYYYMM({time_col}) ORDER BY ({time_col});")
    # Insert by reading parquet and sending as list of tuples
    for f in files:
        df = pd.read_parquet(f, engine="pyarrow")
        df.columns = [c for c in df.columns]
        data = [tuple(x) for x in df.itertuples(index=False, name=None)]
        client.execute(f"INSERT INTO {database}.{table} VALUES", data, types_check=True)
    print("Carga a ClickHouse finalizada.")

if __name__ == "__main__":
    main()
