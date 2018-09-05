########
autoboto
########

======
Status
======

**Alpha**

=============
The Objective
=============

    I want to be able to write boto3 code with my favourite IDE (PyCharm) telling me that the ``s3`` service
    has methods called ``list_buckets`` and ``list_objects_v2`` and they take certain arguments
    and return objects of this or that type which has these attributes of these types.

**autoboto** allows me to do that:

.. code-block:: python

    from autoboto.services import s3

    s3_client = s3.Client()

    for bucket in s3_client.list_buckets().buckets:
        print(f"= {bucket.name} =")
        for obj in s3_client.list_objects_v2(bucket_name=bucket.name).contents:
            print(f"  - {obj.key}")

============
Installation
============

.. code-block:: shell

    pip install autoboto


===============
Code Generation
===============

When you install **autoboto** from pypi.org, it already contains generated code for all the services
that boto3 supports.

This is only useful if you're changing the generated code and want to experiment with **autoboto**.

.. code-block:: shell

    python -m autoboto.builder --services s3,cloudformation,lambda

=======
Release
=======

.. code-block:: shell

    bumpversion

    pytest
    flake8
    isort

    # Check everything generates well without formatting
    python -m autoboto.builder --yapf-style "" --services "*"

    # Generate with formatting
    python -m autoboto.builder --yapf-style "facebook" --services "*"

    python setup.py sdist bdist_wheel

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

    twine upload dist/*

    # tag the release
