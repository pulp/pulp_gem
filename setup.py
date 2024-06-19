#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("requirements.txt") as requirements:
    requirements = requirements.readlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="pulp-gem",
    version="0.7.0.dev",
    description="Gemfile plugin for the Pulp Project",
    long_description=long_description,
    license="GPLv2+",
    author="Pulp Project Developers",
    author_email="pulp-dev@redhat.com",
    url="https://pulpproject.org/",
    python_requires=">=3.9",
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=(
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ),
    entry_points={"pulpcore.plugin": ["pulp_gem = pulp_gem:default_app_config"]},
    project_urls={
        "Documentation": "https://docs.pulpproject.org/pulp_gem/",
        "Source": "https://github.com/pulp/pulp_gem",
        "Tracker": "https://github.com/pulp/pulp_gem/issues",
    },
)
