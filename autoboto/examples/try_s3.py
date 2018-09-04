import boto3

from autoboto.services.s3.client import Client

boto_s3_client = boto3.client("s3")

# Print up to one key per bucket
s3 = Client()
for bucket in s3.list_buckets().buckets:
    print(bucket.name)
    for obj in s3.list_objects_v2(bucket=bucket.name).contents:
        print(f" - {obj.key}")
        break
