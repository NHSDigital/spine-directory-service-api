from distutils.core import setup

import setuptools

setup(
    name='spine-directory-service-common',
    version='',
    packages=setuptools.find_packages(),
    url='',
    license='',
    author='NIA Development Team',
    author_email='',
    description='Common utilities used by the NHS integration adaptors projects.',
    install_requires=[
        'defusedxml~=0.6',
        'aioboto3~=8.0',
        'tornado~=6.0',
        'pystache~=0.5',
        'lxml~=4.4',
        'python-qpid-proton~=0.28',
        'motor~=2.1',
        'isodate~=0.6'
    ]
)