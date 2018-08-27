########
autoboto
########

*A proof of concept, only tried with s3 service.*

**autoboto** generates code to make **boto3** easy to use:

* auto-complete works in PyCharm
* service methods return dataclass instances with all attributes known to your IDE

.. code-block:: python

    import boto3

    from autoboto.services.s3 import Client

    boto_s3_client = boto3.client("s3")

    # Print up to one key per bucket
    s3 = Client()
    for bucket in s3.list_buckets().Buckets:
        print(bucket.Name)
        for obj in s3.list_objects_v2(Bucket=bucket.Name).Contents:
            print(f" - {obj.Key}")
            break


**autoboto** only works on Python 3.6+ because we like *f-strings*.
