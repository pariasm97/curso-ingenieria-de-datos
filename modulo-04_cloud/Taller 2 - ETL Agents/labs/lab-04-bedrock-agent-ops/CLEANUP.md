# Cleanup - Lab 04

1. Elimine el stack del Lab 04.
2. Elimine o despublique el Agent y Action Group en Bedrock si ya no se usa.
3. Elimine el zip subido a S3 si aplica:

```bash
aws s3 rm s3://<ArtifactsBucketName>/lambdas/lab-04/bedrock_agent_fulfillment.zip
```
