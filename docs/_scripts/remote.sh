# Create a remote that syncs all versions of panda into your repository.
pulp gem remote create --name gem --url https://index.rubygems.org/ --includes '{"panda":null}'
