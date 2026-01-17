# Cleanup - Lab 01

1. Elimine el stack del Lab 01 (Glue Job).
2. Si desea limpiar datos generados:

```bash
aws s3 rm s3://<DataBucketName>/silver/ --recursive
```

3. Si desea borrar el script subido:

```bash
aws s3 rm s3://<ArtifactsBucketName>/scripts/lab-01/glue_entity_raw_to_silver.py
```
