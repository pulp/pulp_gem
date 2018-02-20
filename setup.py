#!/usr/bin/env python3

from setuptools import setup, find_packages

requirements = [
    'pulpcore-plugin',
]

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pulp-gem',
    version='0.0.1a1',
    description='Gemfile plugin for the Pulp Project',
    long_description=long_description,
    author='Matthias Dellweg',
    author_email='dellweg@atix.de',
    url='https://github.com/ATIX-AG/pulp_gem',
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=['test']),
    entry_points={
        'pulpcore.plugin': [
            'pulp_gem = pulp_gem:default_app_config',
        ]
    }
)
