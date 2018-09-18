########
autoboto
########

============
Installation
============

.. code-block:: shell

    pip install autoboto

============
Introduction
============

* Project Status: **Alpha**. You should use this only for ad-hoc queries when exploring
  the AWS. It's for people who roughly know what they want from AWS, but don't want to
  scroll up and down the long (and good) boto3 documentation pages to find out the
  right method and parameter names. We are in the 21st century and for user-facing code,
  the auto-complete should work.

* All response objects are dataclasses.

* All response objects have a ``response_metadata`` which is an unmodified dictionary
  normally returned under the ``ResponseMetadata`` key of the response dictionary.

* Passing nested objects isn't as easy as passing nested dictionaries, but it has benefits.

* The method names are as in boto3, but parameter names have been changed from ``CamelCase``
  to ``snake_case``.

* Custom methods that boto3 does not generate from botocore (for example, ``s3.upload_file``
  are simply delegated to the boto3 client and have no documentation available (for now).
  The parameter names are as in the original methods.

.. code-block:: python

    from autoboto.services import s3

    s3_client = s3.Client()

    for bucket in s3_client.list_buckets().buckets:
        print(bucket.name)
        for obj in s3_client.list_objects_v2(bucket_name=bucket.name).contents:
            print(f" - {obj.key}")

You can also paginate:

.. code-block:: python

    for page in s3_client.list_objects_v2(bucket_name=bucket.name).paginate():
        for obj in page.contents:
            print(f" - {obj.key}")


===============
Code Generation
===============

**You don't need to read this section**. It's about how to generate the autoboto code.

When you install ``autoboto`` from pypi.org, the package already contains the generated code for all the services
that boto3 supports.

If you want to re-generate the code, you can do so with the included ``botogen``.

Code generation includes importing the generated modules and instantiating the generated client classes.
For this to work you will need to have ``AWS_PROFILE`` environment variable pointing too an AWS profile which
has ``region`` set.

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

Do not use any imports from ``botogen.autoboto_template`` in tests of the generated code
because the generated code does not import from there. Instead, use the dedicated fixtures
(for which, ironically, the auto-complete won't work).

-----
Tests
-----

``tests`` directory contains both unit tests and integration tests. For unit tests you don't need an AWS account.

.. code-block:: shell

    pytest tests/unit

To run tests across multiple Python versions, use tox. To run ``tox``, you need to first generate
the autoboto package or it will fail.

If you're using ``pyenv`` and virtualenvs, don't run ``tox`` from within a virtualenv.

