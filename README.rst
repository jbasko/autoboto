########
autoboto
########

What is awesome:

* boto3
* Amazon Web Services design and metadata

What is not awesome:

* Working with classes about which you don't know
  what methods they have and what these methods return.

And when you know that they return ``dict``'s, do you
really want to work with them?

We don't. We like objects with a clear set of attributes
which our favourite IDE (PyCharm) auto-suggests us.

**autoboto** generates code around **boto3** to achieve
this.


.. code-block:: python

    from build.services.s3 import operations as ops

    for bucket in ops.ListBuckets().execute().Buckets:
        print(f"Contents of {bucket}:")
        for obj in ops.ListObjectsV2(Bucket=bucket.Name).execute().Contents:
            print(f" - {obj.Key}: {obj}")
            break
