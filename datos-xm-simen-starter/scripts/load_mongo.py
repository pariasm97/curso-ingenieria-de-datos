import os, click, pandas as pd
from glob import glob
from pymongo import MongoClient

def list_parquet_files(parquet_dir):
    return sorted([p for p in glob(os.path.join(parquet_dir, "**", "*.parquet"), recursive=True)])

@click.command()
@click.option("--parquet-dir", required=True)
@click.option("--mongo-uri", default="mongodb://localhost:27017")
@click.option("--database", default="energy")
@click.option("--collection", default="demanda")
def main(parquet_dir, mongo_uri, database, collection):
    files = list_parquet_files(parquet_dir)
    if not files:
        raise click.ClickException(f"No hay parquet en {parquet_dir}")
    client = MongoClient(mongo_uri)
    coll = client[database][collection]
    for f in files:
        df = pd.read_parquet(f, engine="pyarrow")
        recs = df.to_dict(orient="records")
        if recs:
            coll.insert_many(recs)
    # índice simple
    coll.create_index([("fecha", 1)])
    print("Carga a Mongo finalizada.")

if __name__ == "__main__":
    main()
