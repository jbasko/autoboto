from autoboto.services import s3

# Print up to one key per bucket
s3_client = s3.Client()

for bucket in s3_client.list_buckets().buckets:
    print(bucket.name)
    for obj in s3_client.list_objects_v2(bucket=bucket.name).contents:
        print(f" - {obj.key}")
        break
