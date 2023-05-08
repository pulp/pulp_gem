#!/usr/bin/env bash

# Install gem client before running the test
SCENARIOS=("pulp" "performance" "azure" "gcp" "s3" "stream" "generate-bindings" "lowerbounds")
if [[ " ${SCENARIOS[*]} " =~ " ${TEST} " ]]; then
  cmd_prefix dnf install -yq gem
fi
