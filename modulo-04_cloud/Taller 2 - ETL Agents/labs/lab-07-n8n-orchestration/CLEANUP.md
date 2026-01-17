# Cleanup - Lab 07

1. Baje n8n:

```bash
docker compose down
```

2. Elimine el stack del Lab 07.
3. Elimine el zip subido a S3 si desea:

```bash
aws s3 rm s3://<ArtifactsBucketName>/lambdas/lab-07/n8n_bridge_lambda.zip
```
