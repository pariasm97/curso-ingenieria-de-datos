# Cleanup - Lab 00

1. Vacie los buckets (data y artifacts):

```bash
aws s3 rm s3://<DataBucketName> --recursive
aws s3 rm s3://<ArtifactsBucketName> --recursive
```

2. Elimine el stack de CloudFormation del Lab 00.

Nota: si el stack no elimina por objetos remanentes en S3, repita el paso 1.
