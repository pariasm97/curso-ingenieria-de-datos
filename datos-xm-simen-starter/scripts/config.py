import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "energy")

MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "changeme123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datalake")

SIMEM_BASE = os.getenv("SIMEM_BASE", "https://www.simem.co/backend-files/api/PublicData")
SIMEM_DATASET_ID = os.getenv("SIMEM_DATASET_ID", "e007fb")
START_DATE = os.getenv("START_DATE", "2024-01-01")
END_DATE = os.getenv("END_DATE", "2024-01-07")
RAW_DIR = os.getenv("RAW_DIR", "./data/raw")
