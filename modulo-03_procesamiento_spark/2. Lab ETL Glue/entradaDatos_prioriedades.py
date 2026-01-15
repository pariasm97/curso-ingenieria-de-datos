import boto3
import urllib3


def lambda_handler(event, context):
    http = urllib3.PoolManager()

    # 1. TU ENLACE (Asegúrate que termine en output=xlsx)
    url = ""

    # 2. CONFIGURACIÓN S3
    bucket_name = ""

    file_name = ""

    # 3. DESCARGAR (GET REQUEST)
    response = http.request('GET', url)

    if response.status == 200:
        s3 = boto3.client('s3')

        # 4. SUBIR A S3
        # Body=response.data contiene los bytes crudos del Excel
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=response.data,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        return {
            'statusCode': 200,
            'body': f"Excel guardado en s3://{bucket_name}/{file_name}"
        }
    else:
        raise Exception(f"Error al descargar: {response.status}")
