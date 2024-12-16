#!/bin/bash

# WARNING: DO NOT EDIT!
#
# This file was generated by plugin_template, and is managed by it. Please use
# './plugin-template --github pulp_gem' to update this file.
#
# For more info visit https://github.com/pulp/plugin_template

set -euv

# make sure this script runs at the repo root
cd "$(dirname "$(realpath -e "$0")")"/../../..

VERSION="$1"

if [[ -z "${VERSION}" ]]
then
  echo "No version specified."
  exit 1
fi

mkdir -p ~/.gem
touch ~/.gem/credentials
echo "---
:rubygems_api_key: ${RUBYGEMS_API_KEY}" > ~/.gem/credentials
sudo chmod 600 ~/.gem/credentials
gem push "pulp_gem_client-${VERSION}.gem"
