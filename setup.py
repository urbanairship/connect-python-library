from setuptools import setup

__about__ = {}

with open("uaconnect/__about__.py") as fp:
    exec(fp.read(), None, __about__)

setup(
    name="uaconnect",
    version=__about__["__version__"],
    author="Airship Tools",
    author_email="tools@airship.com",
    url="https://airship.com/",
    description="Python package for using Airship Real-Time Data Streaming",
    long_description=open("README.rst").read(),
    license="Apache v2",
    packages=["uaconnect", "uaconnect.ext"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
    ],
    install_requires=[
        "requests>=2.27",
    ],
)
