#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import find_packages, setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="autoboto",
    version=read("autoboto/__init__.py").split("\n")[0].split("=", 1)[1].strip().strip('"'),
    author="Jazeps Basko",
    author_email="jazeps.basko@gmail.com",
    maintainer="Jazeps Basko",
    maintainer_email="jazeps.basko@gmail.com",
    license="MIT",
    url="https://github.com/jbasko/autoboto",
    description="boto3 with auto-complete and dataclasses not dicts",
    long_description=read("docs/README.rst"),
    packages=find_packages("."),

    install_requires=[
        "boto3",
        "dataclasses",
    ],
    # extras_require={
    #     "botogen": [
    #         "botocore==1.10.84",
    #         "html2text==2018.1.9",
    #         "wr_profiles=3.0.0",
    #         "yapf==0.23.0",
    #     ],
    # },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
    ],
)
