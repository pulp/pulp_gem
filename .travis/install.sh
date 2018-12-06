#!/usr/bin/env bash
set -veuo pipefail

if [ "$TRAVIS_PULL_REQUEST" = "false" ]
then
  PULP_PR_NUMBER=
else
  PR_MSG=$(http --json "https://api.github.com/repos/${TRAVIS_REPO_SLUG}/pulls/${TRAVIS_PULL_REQUEST}" | jq -r .body)
  PULP_PR_NUMBER=$(echo $PR_MSG | sed -n 's/.*pulp\/pulp#\([0-9]*\)/\1/p')
  PULP_PLUGIN_PR_NUMBER=$(echo $PR_MSG | sed -n 's/.*pulp\/pulpcore-plugin#\([0-9]*\)/\1/p')
fi



pip install -r test_requirements.txt

pushd ..
git clone https://github.com/pulp/pulp.git

if [ -n "$PULP_PR_NUMBER" ]; then
  pushd pulp
  git fetch origin +refs/pull/$PULP_PR_NUMBER/merge
  git checkout FETCH_HEAD
  popd
fi
pushd pulp/pulpcore/ && pip install -e . && popd

git clone https://github.com/pulp/pulpcore-plugin.git
if [ -n "$PULP_PLUGIN_PR_NUMBER" ]; then
  pushd pulpcore-plugin
  git fetch origin +refs/pull/$PULP_PLUGIN_PR_NUMBER/merge
  git checkout FETCH_HEAD
  popd
fi
pushd pulpcore-plugin && pip install -e .  && popd

popd
pip install -e .
