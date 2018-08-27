import boto3

from build.services.s3 import operations as ops
from build.services.s3 import Client
from build.services.s3.shapes import Bucket

boto_s3_client = boto3.client("s3")

#
# First implementation:
#
for bucket in ops.ListBuckets().execute(client=boto_s3_client).Buckets:
    print(f"Contents of {bucket}:")
    for obj in ops.ListObjectsV2(Bucket=bucket.Name).execute(client=boto_s3_client).Contents:
        print(f" - {obj.Key}: {obj}")
        break


# #
# # Second implementation:
# #
#
# s3 = Client()
# for bucket in s3.list_buckets():
#     assert isinstance(bucket, Bucket)
#     for obj in s3.list_objects_v2(Bucket=bucket.Name):
#         print(obj)
#         break
