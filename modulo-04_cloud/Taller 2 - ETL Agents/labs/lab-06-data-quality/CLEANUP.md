# Cleanup - Lab 06

1. Elimine el stack del Lab 06.
2. Limpie reportes si desea:

```bash
aws s3 rm s3://<DataBucketName>/quality/ --recursive
```

3. Elimine el script subido:

```bash
aws s3 rm s3://<ArtifactsBucketName>/scripts/lab-06/glue_entity_raw_to_silver_with_quality.py
```
