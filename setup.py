#!/usr/bin/env python3

from setuptools import setup, find_packages

requirements = [
    'pulpcore-plugin>=0.1.0b14',
    'rubymarshal',
]

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pulp-gem',
    version='0.0.1b1',
    description='Gemfile plugin for the Pulp Project',
    long_description=long_description,
    author='Matthias Dellweg',
    author_email='dellweg@atix.de',
    url='https://github.com/ATIX-AG/pulp_gem',
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=['test']),
    classifiers=(
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
    entry_points={
        'pulpcore.plugin': [
            'pulp_gem = pulp_gem:default_app_config',
        ]
    }
)
