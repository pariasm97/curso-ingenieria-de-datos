import os, click, pandas as pd
from glob import glob
import boto3
from botocore.exceptions import ClientError

def list_parquet_files(parquet_dir):
    return sorted([p for p in glob(os.path.join(parquet_dir, "**", "*.parquet"), recursive=True)])

@click.command()
@click.option("--parquet-dir", required=True)
@click.option("--endpoint-url", default="http://localhost:8000")
@click.option("--region", default="us-east-1")
@click.option("--table", default="EnergyDaily")
@click.option("--pk", default="pk")
@click.option("--sk", default="sk")
@click.option("--time-col", default="fecha", help="Usado para construir PK/SK por día")
@click.option("--region-col", default=None, help="Columna de región/zona si existe")
def main(parquet_dir, endpoint_url, region, table, pk, sk, time_col, region_col):
    files = list_parquet_files(parquet_dir)
    if not files:
        raise click.ClickException(f"No hay parquet en {parquet_dir}")
    ddb = boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name=region,
                         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "localstack"),
                         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "localstack"))
    # create table if not exists
    try:
        ddb.create_table(
            TableName=table,
            KeySchema=[{"AttributeName": pk, "KeyType": "HASH"}, {"AttributeName": sk, "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": pk, "AttributeType": "S"}, {"AttributeName": sk, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        ).wait_until_exists()
        print(f"Tabla {table} creada.")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise
    tbl = ddb.Table(table)
    # write a few daily aggregates as example
    import pandas as pd
    all_df = []
    for f in files:
        df = pd.read_parquet(f, engine="pyarrow")
        if time_col not in df.columns:
            continue
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        if df[time_col].isna().all():
            continue
        if region_col and region_col in df.columns:
            g = df.groupby([df[time_col].dt.date, df[region_col]]).size().reset_index(name="n")
            g.rename(columns={time_col: "date", region_col: "region"}, inplace=True)
        else:
            g = df.groupby(df[time_col].dt.date).size().reset_index(name="n")
            g["region"] = "ALL"
        all_df.append(g)
    if not all_df:
        print("No se generaron agregados (verifique columnas).")
        return
    agg = pd.concat(all_df).groupby(["level_0","region"], as_index=False).sum()
    agg.rename(columns={"level_0": "date"}, inplace=True)
    with tbl.batch_writer() as batch:
        for _, row in agg.iterrows():
            date_str = str(row["date"])
            region_val = str(row["region"])
            item = {
                pk: f"REGION#{region_val}",
                sk: f"DAY#{date_str}",
                "count": int(row["n"]),
            }
            batch.put_item(Item=item)
    print(f"Escritos {len(agg)} items en {table}.")

if __name__ == "__main__":
    main()
