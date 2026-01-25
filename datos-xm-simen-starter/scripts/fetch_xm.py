import json, sys, os
from datetime import datetime
from urllib.parse import urlencode
import click
import pandas as pd
import requests

from config import SIMEM_BASE, RAW_DIR
from utils import ensure_dir, write_partitioned_parquet

@click.command()
@click.option("--source", type=click.Choice(["simem"]), default="simem", show_default=True, help="Origen de datos")
@click.option("--dataset-id", required=True, help="Identificador del dataset en SiMEM (ej. e007fb)")
@click.option("--start-date", required=True, help="YYYY-MM-DD")
@click.option("--end-date", required=True, help="YYYY-MM-DD")
@click.option("--out-dir", default=RAW_DIR, show_default=True, help="Directorio base para guardar Parquet")
@click.option("--time-col", default="fecha", show_default=True, help="Nombre de la columna temporal en el dataset")
def main(source, dataset_id, start_date, end_date, out_dir, time_col):
    """Descarga datos desde SiMEM (API pública) y escribe Parquet particionado por fecha."""
    if source != "simem":
        raise click.ClickException("Solo 'simem' está implementado en este starter.")
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "datasetId": dataset_id,
        "columnDestinyName": "null",
        "values": "null",
    }
    url = f"{SIMEM_BASE}?{urlencode(params)}"
    r = requests.get(url, timeout=120)
    if r.status_code != 200:
        raise click.ClickException(f"Solicitud falló: {r.status_code} {r.text[:240]}")
    try:
        data = r.json()
    except Exception:
        # algunos endpoints devuelven JSON anidado en texto
        data = json.loads(r.text)
    # normaliza en DataFrame
    if isinstance(data, dict) and "parameters" in data:
        # algunos endpoints envuelven en 'parameters'/'data'
        payload = data.get("data") or data.get("result") or []
    elif isinstance(data, list):
        payload = data
    else:
        payload = data
    if not payload:
        raise click.ClickException("Respuesta vacía del API. Verifique dataset_id y rango de fechas.")
    df = pd.json_normalize(payload)
    if time_col not in df.columns:
        # intenta inferir
        cand = [c for c in df.columns if c.lower() in ("fecha", "fechahora", "datetime", "date", "time")]
        if cand:
            time_col = cand[0]
        else:
            raise click.ClickException(f"No encuentro columna temporal. Campos: {list(df.columns)[:20]} ...")
    print(f"Columnas: {list(df.columns)}")
    ensure_dir(out_dir)
    parts = write_partitioned_parquet(df, out_dir, dataset_id, date_col=time_col)
    print(f"Escritos {len(parts)} archivos Parquet bajo {out_dir}/{dataset_id}")

if __name__ == "__main__":
    main()
