#!/usr/bin/env bash
set -veuo pipefail

PULP_PR_NUMBER=
PULP_PLUGIN_PR_NUMBER=
if [ -f DONOTMERGE.requirements ]
then
  source DONOTMERGE.requirements
fi

pip install -r test_requirements.txt

pushd ..

git clone https://github.com/pulp/pulp.git
pushd pulp
if [ -n "$PULP_PR_NUMBER" ]; then
  echo "=== Using pulp PR #${PULP_PR_NUMBER} ==="
  git fetch origin +refs/pull/$PULP_PR_NUMBER/merge
  git checkout FETCH_HEAD
fi
pip install -e .
popd

git clone https://github.com/pulp/pulpcore-plugin.git
pushd pulpcore-plugin
if [ -n "$PULP_PLUGIN_PR_NUMBER" ]; then
  echo "=== Using pulpcore-plugin PR #${PULP_PLUGIN_PR_NUMBER} ==="
  git fetch origin +refs/pull/$PULP_PLUGIN_PR_NUMBER/merge
  git checkout FETCH_HEAD
fi
pip install -e .
popd

popd
pip install -e .
