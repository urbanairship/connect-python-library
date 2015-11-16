from setuptools import setup

__about__ = {}

with open("uaconnect/__about__.py") as fp:
    exec(fp.read(), None, __about__)

setup(
    name='uaconnect',
    version=__about__["__version__"],
    author="Adam Lowry",
    author_email="adam@urbanairship.com",
    url="http://urbanairship.com/",
    description="Python package for using Urban Airship Connect",
    long_description=open('README.rst').read(),
    license='Apache v2',
    packages=['uaconnect', 'uaconnect.ext'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'requests>=1.2',
    ],
)
