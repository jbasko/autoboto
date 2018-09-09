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

When you install ``autoboto`` from pypi.org, the package already contains the generated code for all the services
that boto3 supports.

If you want to re-generate the code, you can do so with the included ``botogen``.

.. code-block:: shell

    python -m botogen --services s3,cloudformation,lambda


----------
Components
----------

* ``autoboto`` - package where the generated code is put just before release. Do not add anything there manually.
  All files in this directory may be overwritten.
* ``botogen`` - the code responsible for autoboto generation
* ``botogen.autoboto_template`` - contents of this package end up in the generated ``autoboto`` package.

  * ``.gitignore`` file under ``botogen/autoboto_template`` instructs git to ignore all files in the directory.
    This is so that the generated code in ``autoboto`` package is never added to version control.
    Therefore, during autoboto development, when you are adding new files to the ``botogen/autoboto_template``,
    you need to add ``-f`` flag to force-add them to git.

* ``botogen.indentist`` - generic Python code generator


-------------------
Directory Structure
-------------------

.. code-block:: text

    build/                                  All build artifacts are put here

        release/                            Release builds happen here

            20180909_135602/                individual release build directory; Added to sys.path
                autoboto/                   generated autoboto package; an augmented copy of botogen/autoboto_complete
                    core/
                    examples/
                    services/
                    __init__.py

        test/                               Test builds happen here

            20180909_135330/                individual test build directory; Added to sys.path
                autoboto_20180909_135330/   generated autoboto package; an augmented copy of botogen/autoboto_complete
                    core/
                    examples/
                    services/
                    __init__.py

        test-packages/                      Target directory for test builds -- where the generated
                                            packages are put after successful completion of a build
                                            and tests passing on the generated code.


* ``build_dir`` -- a temporary directory in which all the build artifacts are generated. In the example above,
  ``build/test/20180909_135330`` and ``build/release/20180909_135602`` are build directories.

* ``target_package`` -- name of the generated target package; used in import statements in the generated code.
  ``autoboto`` when generating the release; ``autoboto_{timestamp}`` in tests.

* ``target_dir`` -- the directory in which to put the target package.
  By default it's the current directory, but in tests it is ``build/test-packages``.


-----
Notes
-----

Do not use any imports from ``botogen.autoboto_template`` in tests because the objects that exist there
are not the same that the test code will access.

-------
``tox``
-------

To run ``tox``, you need to first generate the autoboto package or it will fail.
