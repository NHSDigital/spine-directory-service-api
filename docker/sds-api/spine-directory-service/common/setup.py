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
        'tornado~=6.0',
        'isodate~=0.6'
    ]
)
