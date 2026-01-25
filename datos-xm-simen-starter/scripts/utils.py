import os
from pathlib import Path
import pandas as pd

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def write_partitioned_parquet(df: pd.DataFrame, out_base: str, dataset_id: str, date_col: str):
    import pandas as pd
    from pandas.api.types import is_datetime64_any_dtype as is_dt
    if date_col not in df.columns:
        raise ValueError(f"time column '{date_col}' not present in dataframe")
    if not is_dt(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=False)
    df = df.dropna(subset=[date_col])
    df["year"] = df[date_col].dt.year.astype("int32")
    df["month"] = df[date_col].dt.month.astype("int16")
    df["day"] = df[date_col].dt.day.astype("int16")
    # partition path: out_base/dataset_id/year=YYYY/month=MM/day=DD/part-*.parquet
    parts = []
    for (y, m, d), sub in df.groupby(["year", "month", "day"]):
        part_dir = os.path.join(out_base, dataset_id, f"year={y}", f"month={m:02d}", f"day={d:02d}")
        ensure_dir(part_dir)
        part_path = os.path.join(part_dir, f"part-{len(parts):05d}.parquet")
        sub.drop(columns=["year", "month", "day"]).to_parquet(part_path, index=False)
        parts.append(part_path)
    return parts
