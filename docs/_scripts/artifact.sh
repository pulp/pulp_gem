# Get a Gem package or choose your own
curl -O https://fixtures.pulpproject.org/gem/gems/amber-1.0.0.gem

# Upload it to Pulp
pulp gem content upload --file "amber-1.0.0.gem"

CONTENT_HREF=$(pulp gem content list | jq -r .[0].pulp_href)
