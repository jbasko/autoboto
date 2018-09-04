########
autoboto
########

======
Status
======

**Pre-Alpha** (Proof of Concept)

=============
The Objective
=============

I want to be able to write code like below with my favourite IDE (PyCharm) telling me that the ``s3`` service
has methods called ``list_buckets`` and ``list_objects_v2`` and they take certain arguments
and return objects of this or that type.

.. code-block:: python

    from autoboto.services.s3.client import Client

    s3 = Client()

    for bucket in s3.list_buckets().buckets:
        print(f"= {bucket.name} =")
        for obj in s3.list_objects_v2(bucket_name=bucket.name).contents:
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

.. code-block:: shell

    python -m autoboto.builder
