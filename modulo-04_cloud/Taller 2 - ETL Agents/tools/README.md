# Tools

## pack_and_upload.sh

Sube a S3 (bucket de artifacts) los scripts Glue y los zip de Lambdas que requieren los labs.

Uso:

```bash
chmod +x tools/pack_and_upload.sh
./tools/pack_and_upload.sh <ArtifactsBucketName>
```

Nota: requiere AWS CLI configurado.
