# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('../README.md') as f:
    readme = f.read()

with open('../LICENSE') as f:
    license = f.read()

setup(
    name='drasil',
    version='0.1.0',
    description='Static HTML website generator based on directory tree',
    long_description=readme,
    author='Alessio Degani',
    author_email='alessio.degani@gmail.com',
    url='https://github.com/adegani/drasil',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    scripts=["drasil"],
    install_requires=[
        'ddate>=0.1.2',
        'importlib-metadata==1.5.0',
        'pillow'
    ]
)
