from build.services.s3 import operations as ops

for bucket in ops.ListBuckets().execute().Buckets:
    print(f"Contents of {bucket}:")
    for obj in ops.ListObjectsV2(Bucket=bucket.Name).execute().Contents:
        print(f" - {obj.Key}: {obj}")
        break
