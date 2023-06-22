# Distributions are created asynchronously. Create one, and specify the publication that will
# be served at the base path specified.
pulp gem distribution create --name foo --base-path foo --publication "$PUBLICATION_HREF"
