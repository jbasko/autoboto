import boto3

from build.services.s3 import Client

boto_s3_client = boto3.client("s3")

# Print up to one key per bucket
s3 = Client()
for bucket in s3.list_buckets().Buckets:
    print(bucket.Name)
    for obj in s3.list_objects_v2(Bucket=bucket.Name).Contents:
        print(f" - {obj.Key}")
        break
