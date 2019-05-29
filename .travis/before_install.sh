#!/usr/bin/env bash

# WARNING: DO NOT EDIT!
#
# This file was generated by plugin_template, and is managed by bootstrap.py. Please use
# bootstrap.py to update this file.
#
# For more info visit https://github.com/pulp/plugin_template

set -mveuo pipefail

export PRE_BEFORE_INSTALL=$TRAVIS_BUILD_DIR/.travis/pre_before_install.sh
export POST_BEFORE_INSTALL=$TRAVIS_BUILD_DIR/.travis/post_before_install.sh

COMMIT_MSG=$(git log --format=%B --no-merges -1)
export COMMIT_MSG

if [ -f $PRE_BEFORE_INSTALL ]; then
    $PRE_BEFORE_INSTALL
fi

export PULP_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulpcore\/pull\/(\d+)' | awk -F'/' '{print $7}')
export PULP_PLUGIN_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulpcore-plugin\/pull\/(\d+)' | awk -F'/' '{print $7}')
export PULP_SMASH_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/PulpQE\/pulp-smash\/pull\/(\d+)' | awk -F'/' '{print $7}')
export PULP_ROLES_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/ansible-pulp\/pull\/(\d+)' | awk -F'/' '{print $7}')
export PULP_BINDINGS_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulp-openapi-generator\/pull\/(\d+)' | awk -F'/' '{print $7}')
export PULP_OPERATOR_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulp-operator\/pull\/(\d+)' | awk -F'/' '{print $7}')

# test_requirements contains tools needed for flake8, etc.
# So install them here rather than in install.sh
pip install -r test_requirements.txt



# run black separately from flake8 to get a diff
black --check --diff .

# Lint code.
flake8 --config flake8.cfg

cd ..
git clone --depth=1 https://github.com/pulp/ansible-pulp.git
if [ -n "$PULP_ROLES_PR_NUMBER" ]; then
  cd ansible-pulp
  git fetch --depth=1 origin +refs/pull/$PULP_ROLES_PR_NUMBER/merge
  git checkout FETCH_HEAD
  cd ..
fi


git clone --depth=1 https://github.com/pulp/pulp-operator.git
if [ -n "$PULP_OPERATOR_PR_NUMBER" ]; then
  cd pulp-operator
  git fetch --depth=1 origin +refs/pull/$PULP_OPERATOR_PR_NUMBER/merge
  git checkout FETCH_HEAD
  cd ..
fi


git clone --depth=1 https://github.com/pulp/pulpcore.git

if [ -n "$PULP_PR_NUMBER" ]; then
  cd pulpcore
  git fetch --depth=1 origin +refs/pull/$PULP_PR_NUMBER/merge
  git checkout FETCH_HEAD
  cd ..
fi


git clone --depth=1 https://github.com/pulp/pulpcore-plugin.git

if [ -n "$PULP_PLUGIN_PR_NUMBER" ]; then
  cd pulpcore-plugin
  git fetch --depth=1 origin +refs/pull/$PULP_PLUGIN_PR_NUMBER/merge
  git checkout FETCH_HEAD
  cd ..
fi


git clone --depth=1 https://github.com/PulpQE/pulp-smash.git

if [ -n "$PULP_SMASH_PR_NUMBER" ]; then
  cd pulp-smash
  git fetch --depth=1 origin +refs/pull/$PULP_SMASH_PR_NUMBER/merge
  git checkout FETCH_HEAD
  cd ..
fi

# pulp-smash already got installed via test_requirements.txt
pip install --upgrade --force-reinstall ./pulp-smash

pip install ansible

cd pulp_gem

if [ -f $POST_BEFORE_INSTALL ]; then
    $POST_BEFORE_INSTALL
fi
