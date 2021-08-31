"""
Quart-Session
-------------

Quart-Session is an extension for Quart that adds support for
Server-side Session to your application.

Links
`````

* `Github
  <https://github.com/sferdi0/quart-session>`_

"""
from setuptools import setup

with open('README.md') as f:
    long_description = f.read()


INSTALL_REQUIRES = [
    "Quart>=0.10.0"
]

setup(
    name='Quart-Session',
    version='1.0.3',
    url='https://github.com/sferdi0/quart-session',
    license='BSD',
    author='Sander',
    author_email='sander@sanderf.nl',
    description='Adds server-side session support to your Quart application',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['quart_session'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=INSTALL_REQUIRES,
    tests_require=INSTALL_REQUIRES + ["asynctest", "hypothesis", "pytest", "pytest-asyncio"],
    extras_require={
        "dotenv": ["python-dotenv"],
        "redis": ["aioredis>=2.0.0"]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
