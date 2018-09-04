########
autoboto
########

======
Status
======

**Pre-Alpha**

=============
The Objective
=============

I want to be able to write code like below with my favourite IDE (PyCharm) telling me that the ``s3`` service
has methods called ``list_buckets`` and ``list_objects_v2`` and they take certain arguments
and return objects of this or that type.

.. code-block:: python

    import botocomplete.services.s3

    s3 = botocomplete.services.s3.Client()

    for bucket in s3.list_buckets():
        print(f"= {bucket.name} =")
        for obj in s3.list_objects_v2(bucket_name=bucket.name):
            print(f"  - {obj.key}")

============
Installation
============

Not yet.

.. code-block:: shell

    pip install autoboto


===============
Code Generation
===============

.. code-block:: python

    import autoboto

    autoboto.generate(
        services=[
            "s3",
            "cloudformation",
        ],
        style=autoboto.Style(
            # If True all method parameter names and shape attribute names are
            # changed from CamelCase to snake_case:
            #   bucket_name
            # instead of default:
            #   BucketName
            snake_case_variable_names=True,

            # If True generates iterators to allow:
            #   for bucket in s3.list_buckets()
            # instead of default:
            #   for bucket in s3.list_buckets().Buckets
            top_level_iterators=True,
        ),
    )
